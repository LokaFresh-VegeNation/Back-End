import pandas as pd
import numpy as np
import requests, yaml, os
from sklearn.linear_model import LinearRegression
from datetime import datetime

def update_produksi():
    def load_config():
        with open(os.path.join("config.yaml"), "r") as f:
            return yaml.safe_load(f)

    API_ENDPOINTS = {
        "Produksi CR": "https://data.jabarprov.go.id/api-backend/bigdata/distanhor/od_15618_produksi_cabai_rawit_berdasarkan_kabupatenkota_v2",
        "Produksi BM": "https://data.jabarprov.go.id/api-backend/bigdata/distanhor/od_15611_produksi_bawang_merah_berdasarkan_kabupatenkota_v3",
        "Produksi BP": "https://data.jabarprov.go.id/api-backend/bigdata/distanhor/od_15612_produksi_bawang_putih_berdasarkan_kabupatenkota_v4"
    }

    config = load_config()
    FILE_PATH = config['data_paths']['produksi'] 

    def fetch_total_produksi_tahun(url, tahun):
        response = requests.get(url, params={"limit": 1000})
        data = response.json()["data"]
        df = pd.DataFrame(data)
        kolom_produksi = [k for k in df.columns if "produksi" in k][0]
        df = df[df["tahun"] == tahun]
        df["produksi"] = pd.to_numeric(df[kolom_produksi], errors="coerce")
        return df["produksi"].sum()

    def update_data_tahun_lalu(df, tahun_lalu):
        for kolom, url in API_ENDPOINTS.items():
            try:
                total = fetch_total_produksi_tahun(url, tahun_lalu)
                df.loc[df["Year"] == tahun_lalu, kolom] = total
                print(f"[UPDATED] {kolom} untuk tahun {tahun_lalu}: {total}")
            except Exception as e:
                print(f"[ERROR] Gagal update {kolom} tahun {tahun_lalu}: {e}")
        return df

    def prediksi_tahun_ini(df, tahun_ini):
        hasil = {"Year": tahun_ini}
        for kolom in ["Produksi CR", "Produksi BM", "Produksi BP"]:
            temp_df = df.dropna(subset=[kolom])
            X = temp_df[["Year"]]
            y = temp_df[kolom]
            model = LinearRegression()
            model.fit(X, y)
            pred = model.predict([[tahun_ini]])[0]
            hasil[kolom] = round(pred, 2)
            print(f"[PREDIKSI] {kolom} untuk tahun {tahun_ini}: {hasil[kolom]}")
        return hasil

    df = pd.read_csv(FILE_PATH)

    tahun_sekarang = datetime.today().year
    tahun_lalu = tahun_sekarang - 1

    # Update data tahun lalu
    df = update_data_tahun_lalu(df, tahun_lalu)

    # Prediksi tahun ini
    if tahun_sekarang not in df["Year"].values:
        hasil_prediksi = prediksi_tahun_ini(df, tahun_sekarang)
        df = pd.concat([df, pd.DataFrame([hasil_prediksi])], ignore_index=True)
    else:
        print(f"[INFO] Prediksi untuk {tahun_sekarang} sudah ada di data.")

    # Simpan kembali
    df = df.sort_values("Year").reset_index(drop=True)
    df.to_csv(FILE_PATH, index=False)
    print("[DONE] File total_produksi.csv berhasil diperbarui.")