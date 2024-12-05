import os
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
from pymilvus import MilvusClient
import textwrap
from typing import List

# OpenAI API anahtarını alın
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai_client = OpenAI(api_key=OPENAI_API_KEY)
COLLECTION_NAME = "anime_search"
DIMENSION = 1536
BATCH_SIZE = 1000
# Connect to Milvus Database
client = MilvusClient(
    uri="http://localhost:19530",
    token="root:Milvus"
)
# Remove collection if it already exists
if client.has_collection(COLLECTION_NAME):
    client.drop_collection(COLLECTION_NAME)
from pymilvus import DataType

# 1. Create schema
schema = MilvusClient.create_schema(
    auto_id=True,
    enable_dynamic_field=False,
)

# 2. Add fields to schema
schema.add_field(field_name="id", datatype=DataType.INT64, is_primary=True)
schema.add_field(field_name="title", datatype=DataType.VARCHAR, max_length=640)
schema.add_field(field_name="rating", datatype=DataType.VARCHAR, max_length=640)
schema.add_field(field_name="number_of_rating", datatype=DataType.VARCHAR, max_length=640)
schema.add_field(field_name="image", datatype=DataType.VARCHAR, max_length=6400)
schema.add_field(field_name="description", datatype=DataType.VARCHAR, max_length=64000)
schema.add_field(field_name="embedding", datatype=DataType.FLOAT_VECTOR, dim=DIMENSION)

# 3. Create collection with the schema
client.create_collection(collection_name=COLLECTION_NAME, schema=schema)


# 1. Prepare index parameters
index_params = client.prepare_index_params()

# 2. Add an index on the embedding field
index_params.add_index(
    field_name="embedding", metric_type="IP", index_type="AUTOINDEX", params={}
)

# 3. Create index
client.create_index(collection_name=COLLECTION_NAME, index_params=index_params)

# 4. Load Collection
client.load_collection(collection_name=COLLECTION_NAME)

import pandas as pd

df = pd.read_csv('../anime_data.csv')

df["Rating"] = df["Rating"].astype(str)
df["Number of Episodes"] = df["Number of Episodes"].astype(str)
df["Image"] = df["Image"].astype(str)
df['Name'] = df['Name'].str.replace(r'^\d+\.\s*', '', regex=True)




def emb_texts(texts):
    res = openai_client.embeddings.create(input=texts, model="text-embedding-3-small")
    return [res_data.embedding for res_data in res.data]

from tqdm import tqdm
# batch (data to be inserted) is a list of dictionaries
batch = []
# Embed and insert in batches
for i in tqdm(range(0, len(df))):
    batch.append(
        {
            "title": df.iloc[i]["Name"] or "",
            "image": df.iloc[i]["Image"] or "",
            "number_of_rating": df.iloc[i]["Number of Episodes"] or "",
            "rating": df.iloc[i]["Rating"] or "",
            "description": df.iloc[i]["Description"] or "",
        }
    )

    if len(batch) % BATCH_SIZE == 0 or i == len(df) - 1:
        embeddings = emb_texts([item["description"] for item in batch])

        for item, emb in zip(batch, embeddings):
            item["embedding"] = emb

        client.insert(collection_name=COLLECTION_NAME, data=batch)
        batch = []


import textwrap


# Query Model
class QueryRequest(BaseModel):
    query: str
    top_k: int

app = FastAPI()
from fastapi.middleware.cors import CORSMiddleware

# CORS ayarları
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Herhangi bir kaynaktan erişime izin verir
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/search/")
async def search_anime(query_request: QueryRequest):
    query = query_request.query
    top_k = query_request.top_k
    text = query

    res = client.search(
        collection_name=COLLECTION_NAME,
        data=emb_texts(text),
        limit=top_k,
        output_fields=["title", "image", "number_of_rating", "rating", "description"],
        search_params={
            "metric_type": "IP",
            "params": {},
        },
    )

    results = []
    for hit_group in res:
        for rank, hit in enumerate(hit_group, start=1):
            entity = hit["entity"]
            results.append({
                "Rank": rank,
                "Score": hit['distance'],
                "Title": entity.get('title', ''),
                "Image": entity.get('image', ''),
                "Number of Rating": entity.get('number_of_rating', ''),
                "Rating": entity.get('rating', ''),
                "Description": textwrap.fill(entity.get("description", ""), width=88)
            })

    return {"results": results}


my_query = ("anime about fighting with monsters")
