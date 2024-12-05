import React, { useState } from "react";
import axios from "axios";
import './App.css';

function App() {
  const [query, setQuery] = useState("");
  const [topK, setTopK] = useState(5); // Top k default olarak 5
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  // Backend API endpoint
  const API_URL = "http://127.0.0.1:8000/search/";

  // Kullanıcı sorgusunu gönder
  const handleSearch = async () => {
    if (!query) return;  // Sorgu boş olmamalı

    setLoading(true); // Yükleniyor durumuna al
    try {
      const response = await axios.post(API_URL, { query, top_k: topK });
      setResults(response.data.results);
    } catch (error) {
      console.error("Error fetching data", error);
    } finally {
      setLoading(false); // Yükleme işlemi bitti
    }
  };

  return (
    <div className="App">
      <h1>Anime Movie Search</h1>
      
      {/* Sorgu input alanı */}
      <div className="search-container">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search for an anime..."
        />
        
        {/* Top_k input alanı */}
        <input
          type="number"
          value={topK}
          onChange={(e) => setTopK(e.target.value)}
          min="1"
          max="100"
          placeholder="Top K"
        />

        <button onClick={handleSearch}>Search</button>
      </div>

      {/* Yükleniyor durumu */}
      {loading && <p>Loading...</p>}

      {/* Sonuçlar */}
      <div className="results-container">
        {results.length > 0 ? (
          results.map((result, index) => (
            <div key={index} className="result-item">
              <h3>{result.Title}</h3>
              <img src={result.Image} alt={result.Title} className="movie-image" />
              <p>Rating: {result.Rating} ({result["Number of Rating"]})</p>
              <pre>{result.Description}</pre>
            </div>
          ))
        ) : (
          <p>No results found.</p>
        )}
      </div>
    </div>
  );
}

export default App;
