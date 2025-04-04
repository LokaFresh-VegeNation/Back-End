from app import app
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

class Predict : 
    def predict_linear_reg(file_path, num_days):
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