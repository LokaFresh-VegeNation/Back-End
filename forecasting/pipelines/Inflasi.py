import pandas as pd
import requests, yaml
from prophet import Prophet
from datetime import datetime
from dateutil.relativedelta import relativedelta

def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

API_KEY = "251f4ddc2af447c55b54a6d5ce564950"
API_URL = f"https://webapi.bps.go.id/v1/api/list/model/data/lang/ind/domain/3200/var/46/key/{API_KEY}"

config = load_config()
FILE_PATH = config['data_paths']['inflasi'] 

def get_bps_data():
    try:
        res = requests.get(API_URL)
        return res.json()
    except:
        return None

def extract_inflasi_value(json_data, year, month):
    tahun_map = {int(item['label']): item['val'] for item in json_data['tahun']}
    bulan_val_map = {i: val for i, val in zip(range(1, 13), range(156, 168))}

    tahun_val = tahun_map.get(year)
    bulan_val = bulan_val_map.get(month)

    kode_kunci = f"3200460{tahun_val}{bulan_val}"
    return json_data["datacontent"].get(kode_kunci)

def predict_month(df, target_date):
    df_prophet = df.copy()
    df_prophet['ds'] = pd.to_datetime(df_prophet['Date'], format="%Y-%m")
    df_prophet = df_prophet[['ds', 'Inflasi']]
    df_prophet.rename(columns={'Inflasi': 'y'}, inplace=True)

    model = Prophet()
    model.fit(df_prophet)

    future = pd.DataFrame({'ds': [target_date]})
    forecast = model.predict(future)
    return round(forecast.iloc[0]['yhat'], 2)

def update_inflasi():
    today = datetime.today()

    # Target: bulan lalu & bulan ini
    last_month = today.replace(day=1) - relativedelta(months=1)
    current_month = today.replace(day=1)

    df = pd.read_csv(FILE_PATH)

    # Ambil dan update data bulan lalu dari BPS
    bps_data = get_bps_data()
    if bps_data:
        inflasi_val = extract_inflasi_value(bps_data, last_month.year, last_month.month)
        month_str = last_month.strftime("%Y-%m")
        if inflasi_val is not None:
            df = df[df['Date'] != month_str]  # hapus jika sudah ada
            df.loc[len(df.index)] = [month_str, inflasi_val]
            print(f"[UPDATE] Inflasi bulan {month_str} diupdate dengan BPS: {inflasi_val}")
        else:
            print(f"[INFO] Data BPS untuk {month_str} belum tersedia.")
    else:
        print("[ERROR] Gagal mengambil data dari API BPS.")

    # Prediksi inflasi untuk bulan ini
    pred_str = current_month.strftime("%Y-%m")
    target_date = current_month

    pred_val = predict_month(df, target_date)
    df = df[df['Date'] != pred_str]  # hapus prediksi lama jika ada
    df.loc[len(df.index)] = [pred_str, pred_val]
    print(f"[PREDICTED] Inflasi {pred_str} diprediksi: {pred_val}")

    # Simpan
    df = df.sort_values(by="Date", key=lambda x: pd.to_datetime(x, format="%Y-%m"))
    df.to_csv(FILE_PATH, index=False)
    print("[DONE] inflasi.csv berhasil diperbarui.")

if __name__ == "__main__":
    update_inflasi()