from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
import time
import pandas as pd

url = "https://www.imdb.com/search/title/?keywords=anime"

options = webdriver.ChromeOptions()
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
driver = webdriver.Chrome(options=options)
driver.get(url)

def safe_find_element(by, value, context=None):
    context = context or driver
    try:
        return context.find_element(by, value)
    except NoSuchElementException:
        return None

for _ in range(20):
    try:
        show_more_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div[3]/section/section/div/section/section/div[2]/div/section/div[2]/div[2]/div[2]/div/span/button"))
        )
        driver.execute_script("arguments[0].click();", show_more_button)
        time.sleep(1)  # Buton sonrası yüklenmesi için bekle
    except Exception as e:
        print("Error clicking the button or no more pages:", e)
        break

# Veriyi saklayacak liste
anime_data = []

# Tüm verileri çek
anime_list = driver.find_elements(By.XPATH, "//ul[contains(@class, 'ipc-metadata-list') and contains(@class, 'detailed-list-view')]/li")
for anime in anime_list:
    try:
        image = safe_find_element(By.XPATH, ".//img", anime).get_attribute("src") if safe_find_element(By.XPATH, ".//img", anime) else None
        name = safe_find_element(By.XPATH, ".//a/h3", anime).text if safe_find_element(By.XPATH, ".//a/h3", anime) else None
        rating = safe_find_element(By.XPATH, ".//span/div/span/span[1]", anime).text if safe_find_element(By.XPATH, ".//span/div/span/span[1]", anime) else None
        number_of_rating = safe_find_element(By.XPATH, ".//span/div/span/span[2]", anime).text if safe_find_element(By.XPATH, ".//span/div/span/span[2]", anime) else None
        raw_description = safe_find_element(By.XPATH, ".//div/div", anime).text if safe_find_element(By.XPATH, ".//div/div", anime) else None
        description = raw_description.splitlines()[-1] if raw_description else None


        anime_data.append({
            "Image": image,
            "Name": name,
            "Rating": rating,
            "Number of Episodes": number_of_rating,
            "Description": description
        })
    except Exception as e:
        print("Error scraping an anime:", e)


# Verileri DataFrame'e çevir
anime_df = pd.DataFrame(anime_data)

# CSV'ye kaydet
anime_df.to_csv("anime_data.csv", index=False)

# Tarayıcıyı kapat
driver.quit()

print(f"Scraping tamamlandı! Toplam {len(anime_data)} anime çekildi. Veriler 'anime_data.csv' dosyasına kaydedildi.")
