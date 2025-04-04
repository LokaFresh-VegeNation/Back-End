from app import app  # Now, app is correctly initialized
from flask import request, jsonify
import pandas as pd
import numpy as np
from app.predict import Predict 
from app.article import Article

DATASETS = {
    "cabai": "datasets/Bawang Cabai Rawit - Clean.xlsx",
    "bawang_merah": "datasets/Bawang Merah - Clean.xlsx",
    "bawang_putih": "datasets/Bawang Putih - Clean.xlsx"
}

@app.route('/linreg/predict', methods=['GET'])
def predict():
    dataset_comodity = request.args.get('comodity')
    num_days = request.args.get('num_days', type=int)

    if dataset_comodity not in DATASETS:
        return jsonify({"error": "Invalid dataset type. Choose from: cabai, bawang_merah, bawang_putih"}), 400

    if not num_days or num_days <= 0:
        return jsonify({"error": "Invalid number of days. Must be a positive integer."}), 400

    file_path = DATASETS[dataset_comodity]

    predictions = Predict.predict_linear_reg(file_path, num_days)

    """
    JSON Response
    {
        {
        "comodity": "cabai",
        "predictions": {
            "2025-04-01": {
                "All Provinces": 65362.66,
                "Jakarta": 72355.31,
                "West Java": 65469.83
            }
        }
    }
    """

    return jsonify({"comodity": dataset_comodity, "predictions": predictions})

@app.route('/get_articles', methods=['GET'])
def get_article():
    try:
        articles = Article.scrap_articles()
        return jsonify({"results": articles}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
