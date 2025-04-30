import numpy as np
import pandas as pd
from tensorflow.keras.models import load_model
import joblib
from datetime import timedelta
class Predict : 
    def predict_lstm(model_path, input_path, scaler_path, last_date_str, num_days):
        # Load model and preprocessing files
        # model = load_model(model_path)
        model = load_model(model_path)
        X_scaled = np.load(input_path)
        scaler_y = joblib.load(scaler_path)
        
        # Create forecast
        window_size = X_scaled.shape[0]  # assume already shaped (window_size, n_features)
        forecast_input = X_scaled.copy()
        forecast = []

        for _ in range(num_days):
            input_batch = forecast_input.reshape(1, window_size, -1)
            pred_scaled = model.predict(input_batch, verbose=0)[0][0]

            # Append next input
            next_input = np.append(forecast_input[1:], [[*forecast_input[-1][:-1], pred_scaled]], axis=0)
            forecast_input = next_input
            forecast.append(pred_scaled)

        forecast_inverse = scaler_y.inverse_transform(np.array(forecast).reshape(-1, 1))

        # Build date range from last known date
        tanggal_awal = pd.to_datetime(last_date_str) + timedelta(days=1)
        tanggal_prediksi = pd.date_range(start=tanggal_awal, periods=num_days)

        # Build result dict
        predictions = {
            str(tanggal.date()): float(harga)
            for tanggal, harga in zip(tanggal_prediksi, forecast_inverse.flatten())
        }

        return predictions
    
# MODEL_PATHS = {
#     "cabai": "app/cr_model.keras"
# }

# SCALER_PATHS = {
#     "cabai": "app/scaler_y_cabai.pkl"
# }

# INPUT_PATHS = {
#     "cabai": "app/X_scaled_cabai.npy"
# }

# LAST_DATES = {
#     "cabai": "2025-04-23"
# }
    
# predictions = Predict.predict_lstm(
#         MODEL_PATHS["cabai"],
#         INPUT_PATHS["cabai"],
#         SCALER_PATHS["cabai"],
#         LAST_DATES["cabai"],
#         14
#     )

# print(predictions)