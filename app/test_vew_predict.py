from statsmodels.tsa.seasonal import STL
import pandas as pd
import numpy as np
from datetime import timedelta
from tensorflow.keras.models import load_model
from sklearn.preprocessing import MinMaxScaler

import os

class PredictNew:
    def predict_lstm(model_path, last_date_str, num_days, comodity):
        # Load model
        model = load_model(model_path)

        # Load CSV
        df = pd.read_csv("data/data_vegenation.csv")

        # Debug: tampilkan nama kolom asli
        print("DEBUG: Original columns ->", df.columns.tolist())

        # Bersihkan header kolom
        df.columns = df.columns.str.strip()

        # Rename agar seragam
        df = df.rename(columns={
            "Temp Avg": "temp",
            "Humidity Avg": "humidity",
            "RR": "rainfall",
            "Inflasi YoY": "inflasi_yoy",
            "Produksi BM": "produksi_bm",
            "Produksi BP": "produksi_bp",
            "Produksi CR": "produksi_cr",
            "Date": "date"
        })

        # Debug: cek ulang nama kolom setelah rename
        print("DEBUG: Renamed columns ->", df.columns.tolist())

        # Pastikan format datetime
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        # Mapping kolom target
        target_map = {
            "cabai": "produksi_cr",
            "bawang_merah": "produksi_bm",
            "bawang_putih": "produksi_bp"
        }

        if comodity not in target_map:
            raise ValueError(f"Komoditas '{comodity}' tidak dikenali.")

        target_col = target_map[comodity]

        # Cek apakah kolom target ada
        if target_col not in df.columns:
            raise ValueError(f"Kolom target '{target_col}' tidak ditemukan di CSV.")

        # STL decomposition
        df_stl = df.set_index('date')
        stl = STL(df_stl[target_col], period=7)
        result = stl.fit()
        df_stl['trend'] = result.trend
        df_stl['seasonal'] = result.seasonal
        df_stl['residual'] = result.resid
        df_stl = df_stl.reset_index()

        # Mapping kolom produksi sebagai fitur
        produksi_feature_map = {
            "cabai": "produksi_cr",
            "bawang_merah": "produksi_bm",
            "bawang_putih": "produksi_bp"
        }
        produksi_col = produksi_feature_map[comodity]
        
        features = ['trend', 'seasonal', 'residual', 'inflasi_yoy',
                    'temp', 'humidity', 'rainfall', produksi_col,
                    'is_tahun_baru', 'is_idul_fitri', 'is_natal']
        
        # Scaling
        scaler_x = MinMaxScaler()
        scaler_y = MinMaxScaler()

        X_scaled = scaler_x.fit_transform(data[features])
        y_scaled = scaler_y.fit_transform(data[target])

        missing = [col for col in features if col not in df_stl.columns]
        if missing:
            raise ValueError(f"Fitur berikut tidak ditemukan: {missing}")

        data = df_stl[features].dropna()
        window_size = 30

        if len(data) < window_size:
            raise ValueError(f"Data tidak cukup. Diperlukan minimal {window_size} baris data.")

        forecast_input = data.values[-window_size:]
        forecast = []

        for _ in range(num_days):
            input_batch = forecast_input.reshape(1, window_size, -1)
            pred = model.predict(input_batch, verbose=0)[0][0]
            last_known = forecast_input[-1].copy()
            forecast_input = np.append(forecast_input[1:], [[*forecast_input[-1][:-1], pred]], axis=0)
            forecast.append(pred)

        forecast_inverse = scaler_y.inverse_transform(np.array(forecast).reshape(-1, 1))

        tanggal_awal = pd.to_datetime(last_date_str) + timedelta(days=1)
        tanggal_prediksi = pd.date_range(start=tanggal_awal, periods=num_days)

        predictions = {
            str(tanggal.date()): float(harga)
            for tanggal, harga in zip(tanggal_prediksi, forecast)
        }

        return predictions