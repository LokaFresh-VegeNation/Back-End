from app import app 
from flask import request, jsonify
import pandas as pd
import numpy as np
from app.predict import Predict 
from app.article import Article
from datetime import datetime, timedelta
import pytz
from pydantic import BaseModel
from chatbot import main
from flask_cors import CORS
CORS(app)

# Start date
start_date = datetime.strptime("2025-03-31", "%Y-%m-%d").date()

# Days difference
days_diff = (datetime.now().date() - start_date).days

# Add days to start date
new_date = start_date + timedelta(days=days_diff)

print(f"Start date plus {days_diff} days is: {new_date}")

MODEL_PATHS = {
    "cabai": "models/cr_model.keras",
    "bawang_merah": "models/bm_model.keras",
    "bawang_putih": "models/bp_model.keras",
}

SCALER_PATHS = {
    "cabai": "models/scaler_y_cabai.pkl",
    "bawang_merah": "models/scaler_y_bawang_merah.pkl",
    "bawang_putih": "models/scaler_y_bawang_putih.pkl",
}

INPUT_PATHS = {
    "cabai": "models/X_scaled_cabai.npy",
    "bawang_merah": "models/X_scaled_bawang_merah.npy",
    "bawang_putih": "models/X_scaled_bawang_putih.npy",
}

LAST_DATES = start_date

@app.route('/lstm/predict', methods=['GET'])
def predict():
    comodity = request.args.get('comodity')
    num_days = days_diff + request.args.get('num_days', type=int)

    if comodity not in MODEL_PATHS:
        return jsonify({"error": "Invalid commodity. Choose from: cabai, bawang_merah, bawang_putih"}), 400

    if not num_days or num_days <= 0:
        return jsonify({"error": "Invalid number of days. Must be a positive integer."}), 400

    predictions = Predict.predict_lstm(
        MODEL_PATHS[comodity],
        INPUT_PATHS[comodity],
        SCALER_PATHS[comodity],
        LAST_DATES,
        num_days
    )

    return jsonify({"comodity": comodity, "predictions": predictions})

@app.route('/get_articles', methods=['GET'])
def get_article():
    """
    JSON Response
    {
    "results": [
        {
            "title": "Wamendag Dyah Roro Esti menanggapi temuan beras premium berisi medium. Ia menegaskan pentingnya pemantauan dan kerja sama dengan Satgas Pangan untuk penindakan.",
            "link": "https://akcdn.detik.net.id/community/media/visual/2025/03/03/wamendag-ri-dyah-roro-1740999615984_43.jpeg?w=250&q=90",
            "description": "Kata Wamendag Soal Temuan Beras Premium Diisi Medium",
            "date": "https://www.detik.com/sumut/berita/d-7851733/kata-wamendag-soal-temuan-beras-premium-diisi-medium",
            "Tanggal": "Rabu, 02 Apr 2025 11:30 WIB"
        }, 
        { ... }
    }
    """
    
    try:
        articles = Article.scrap_articles()
        return jsonify({"results": articles}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/chatbot', methods=['POST'])
def chatbot():
    try:
        data = request.get_json()
        user_message = data.get('message')

        if not user_message:
            return jsonify({"error": "No message provided."}), 400

        # Preprocess and extract info
        response = main.chatbot_run(user_message)

        return jsonify({"response": response}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
