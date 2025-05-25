from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import yaml
import os
from datetime import datetime
import re
import time

def scrape_harga():
    # Load path dari config.yaml
    def load_config():
        with open("config.yaml", "r") as f:
            return yaml.safe_load(f)
        
    # Setup headless mode
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = webdriver.Chrome(options=options)  # pastikan chromedriver sudah terinstal

    url = "https://dashboard.jabarprov.go.id/id/dashboard-static/pangan"
    driver.get(url)

    config = load_config()
    FILE_PATH = config['data_paths']['harga'] 

    # Tunggu dan klik tombol "Bumbu Dasar"
    try:
        bumbu_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Bumbu Dasar')]"))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", bumbu_button)
        time.sleep(1)
        driver.execute_script("arguments[0].click();", bumbu_button)
        time.sleep(3)
    except Exception as e:
        print("Gagal klik tombol Bumbu Dasar:", e)
        driver.quit()
        exit()

    # Ambil elemen yang memuat komoditas
    items = driver.find_elements(By.CLASS_NAME, "d-flex.flex-column")

    # Inisialisasi hasil
    target_commodities = ["Bawang Merah", "Bawang Putih", "Cabe Rawit Merah"]
    results = {}

    for item in items:
        try:
            name = item.find_element(By.CLASS_NAME, "comodity-title").text.strip()
            price = item.find_element(By.CLASS_NAME, "comodity-price").text.strip()
            if name in target_commodities:
                results[name] = price
        except:
            continue

    driver.quit()

    # Ubah nama komoditas ke format kolom
    column_map = {
        "Bawang Merah": "Bawang Merah",
        "Bawang Putih": "Bawang Putih",
        "Cabe Rawit Merah": "Cabai Rawit"
    }

    # Bersihkan harga jadi angka
    def extract_price(text):
        angka = re.findall(r"[\d.]+", text)
        if angka:
            return int(angka[0].replace('.', ''))  # ubah "38.630" jadi 38630
        return None

    # Buat data baris untuk CSV
    today = datetime.now().strftime("%Y-%m-%d")
    row = {"Date": today}

    for name, price in results.items():
        col = column_map.get(name)
        val = extract_price(price)
        if col:
            row[col] = val

    # Cek apakah file sudah ada
    csv_file = FILE_PATH
    file_exists = os.path.isfile(csv_file)

    # Simpan/append ke CSV
    with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=["Date", "Bawang Merah", "Bawang Putih", "Cabai Rawit"])
        
        if not file_exists:
            writer.writeheader()  # tulis header jika file baru
        
        writer.writerow(row)

    print("Data berhasil disimpan ke", csv_file)

update = scrape_harga()