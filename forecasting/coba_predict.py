import numpy as np
import pandas as pd
import tensorflow as tf
import joblib
import yaml
from datetime import datetime, timedelta
import os

# Load config.yaml
def load_config():
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f)

def predict_next_n_days(komoditas, n_days):
    config = load_config()
    # Ambil path dari config
    model_path = config["model_paths"][komoditas]
    scaler_y_path = config["scaler_paths"][komoditas]
    x_scaled_path = config["seq_paths"][komoditas]

    # Load file
    X_scaled = np.load(x_scaled_path)
    print("Shape dari X_scaled:", X_scaled.shape)
    scaler_y = joblib.load(scaler_y_path)
    model = tf.keras.models.load_model(model_path, compile=False)

    # Ambil input terakhir
    window_size = X_scaled.shape[1]
    forecast_input = X_scaled[-1].copy()
    forecast = []

    for _ in range(n_days):
        input_batch = forecast_input.reshape(1, window_size, X_scaled.shape[-1])  # (1, 120, 11)
        # print(input_batch.shape)
        pred_scaled = model.predict(input_batch, verbose=0)[0][0]  # hasil prediksi

        # Salin fitur terakhir (shape: (11,))
        last_input = forecast_input[-1].copy()
        
        # Ganti nilai target (misalnya di posisi terakhir kolom target)
        last_input[-1] = pred_scaled

        # Tambahkan ke window baru
        forecast_input = np.concatenate([forecast_input[1:], [last_input]], axis=0)
        forecast.append(pred_scaled)

    # Inverse transform
    forecast_inverse = scaler_y.inverse_transform(np.array(forecast).reshape(-1, 1))

    # Buat tanggal prediksi
    last_date = datetime.today().date()
    tanggal_prediksi = pd.date_range(start=last_date + timedelta(days=1), periods=n_days)

    hasil_df = pd.DataFrame({
        'tanggal': tanggal_prediksi,
        f'prediksi_{komoditas}': forecast_inverse.flatten()
    })

    predictions = {
        str(tanggal.date()): float(harga)
        for tanggal, harga in zip(tanggal_prediksi, forecast_inverse.flatten())
    }

    print(predictions)
    return predictions

# predict_next_n_days("cr", 15)
