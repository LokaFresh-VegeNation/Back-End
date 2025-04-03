from app import app
from flask import request, jsonify
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

DATASETS = {
    "cabai": "datasets/Bawang Cabai Rawit - Clean.xlsx",
    "bawang_merah": "datasets/Bawang Merah - Clean.xlsx",
    "bawang_putih": "datasets/Bawang Putih - Clean.xlsx"
}

def predict_prices(file_path, num_days):
    """
    Predict future selling prices using Linear Regression.

    Parameters:
    file_path (str): Path to the dataset.
    num_days (int): Number of days to predict.

    Returns:
    dict: Predicted prices with future dates.
    """
    # Load dataset
    df = pd.read_excel(file_path)

    # Convert Date column to numerical values
    df['Date'] = pd.to_datetime(df['Date'])
    df['Days'] = (df['Date'] - df['Date'].min()).dt.days

    # Select features and target variables
    X = df[['Days']]
    y = df[['All Provinces', 'West Java', 'Jakarta']]

    # Train Linear Regression model
    model = LinearRegression()
    model.fit(X, y)

    # Generate future dates
    future_days = np.arange(df['Days'].max() + 1, df['Days'].max() + num_days + 1).reshape(-1, 1)
    predictions = model.predict(future_days)

    # Create predictions dictionary
    future_dates = pd.to_datetime(df['Date'].max()) + pd.to_timedelta(np.arange(1, num_days + 1), unit='D')
    predicted_prices = {
        str(date.date()): {
            "All Provinces": round(prices[0], 2),
            "West Java": round(prices[1], 2),
            "Jakarta": round(prices[2], 2)
        }
        for date, prices in zip(future_dates, predictions)
    }

    return predicted_prices


@app.route('/')
@app.route('/predict', methods=['GET'])
def predict():
    """
    API endpoint to predict prices based on selected dataset.

    Query Parameters:
    - comodity (str): The comodity of dataset (cabai, bawang_merah, bawang_putih).
    - num_days (int): The number of days to predict.

    Returns:
    JSON: Predicted prices.
    """
    # Get user choice from query parameters
    dataset_comodity = request.args.get('comodity')
    num_days = request.args.get('num_days', type=int)

    if dataset_comodity not in DATASETS:
        return jsonify({"error": "Invalid dataset type. Choose from: cabai, bawang_merah, bawang_putih"}), 400

    if not num_days or num_days <= 0:
        return jsonify({"error": "Invalid number of days. Must be a positive integer."}), 400

    # Get the file path of the selected dataset
    file_path = DATASETS[dataset_comodity]

    # Predict future prices
    predictions = predict_prices(file_path, num_days)

    return jsonify({"type": dataset_comodity, "predictions": predictions})

if __name__ == '__main__':
    app.run(debug=True)
