import pandas as pd
import yaml, os
from datetime import datetime, timedelta

def load_config():
    with open(os.path.join("config.yaml"), "r") as f:
        return yaml.safe_load(f)

config = load_config()
paths = config["data_paths"]

cuaca_path = paths["cuaca"]
inflasi_path = paths["inflasi"]
produksi_path = paths["produksi"]
event_path = paths["event"]
harga_path = paths["harga"]
output_path = paths["merged"]

today = datetime.today()
target_date = today - timedelta(days=1)
target_date_str = target_date.strftime("%Y-%m-%d")
target_month_str = target_date.strftime("%Y-%m")
target_year = target_date.year

cuaca_df = pd.read_csv(cuaca_path)
cuaca_row = cuaca_df[cuaca_df["Date"] == target_date_str]

if cuaca_row.empty:
    raise ValueError(f"Tidak ditemukan data cuaca untuk tanggal {target_date_str}")

inflasi_df = pd.read_csv(inflasi_path)
inflasi_row = inflasi_df[inflasi_df["Date"].str.startswith(target_month_str)]

if inflasi_row.empty:
    raise ValueError(f"Tidak ditemukan data inflasi untuk bulan {target_month_str}")

produksi_df = pd.read_csv(produksi_path)
produksi_row = produksi_df[produksi_df["Year"] == target_year]

if produksi_row.empty:
    raise ValueError(f"Tidak ditemukan data produksi untuk tahun {target_year}")

event_df = pd.read_csv(event_path)
event_row = event_df[event_df["Date"] == target_date_str]

if event_row.empty:
    raise ValueError(f"Tidak ditemukan data event untuk tanggal {target_date_str}")

harga_df = pd.read_csv(harga_path)
harga_row = harga_df[harga_df["Date"] == target_date_str]

if harga_row.empty:
    raise ValueError(f"Tidak ditemukan data harga untuk tanggal {target_date_str}")

merged_data = {
    "Date": target_date_str,
    "Temp Avg": cuaca_row["Temp Avg"].values[0],
    "Humidity Avg": cuaca_row["Humidity Avg"].values[0],
    "RR": cuaca_row["RR"].values[0],
    "Inflasi YoY": inflasi_row["Inflasi"].values[0],
    "Produksi BM": produksi_row["Produksi BM"].values[0],
    "Produksi BP": produksi_row["Produksi BP"].values[0],
    "Produksi CR": produksi_row["Produksi CR"].values[0],
    "is_tahun_baru": event_row["is_tahun_baru"].values[0],
    "is_natal": event_row["is_natal"].values[0],
    "is_idul_fitri": event_row["is_idul_fitri"].values[0],
    "Bawang Merah": harga_row["Bawang Merah"].values[0],
    "Bawang Putih": harga_row["Bawang Putih"].values[0],
    "Cabai Rawit": harga_row["Cabai Rawit"].values[0]
}

try:
    output_df = pd.read_csv(output_path)
    output_df = pd.concat([output_df, pd.DataFrame([merged_data])], ignore_index=True)
except FileNotFoundError:
    output_df = pd.DataFrame([merged_data])  # Buat baru jika belum ada

output_df.to_csv(output_path, index=False)
print(f"Data tanggal {target_date_str} berhasil ditambahkan ke {output_path}")