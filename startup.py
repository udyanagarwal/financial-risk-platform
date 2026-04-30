import os
import sys

print("Running startup - training models...")

# Train volatility models
from app.models.volatility import train_model as train_volatility
from app.models.anomaly import train_anomaly_model

STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS"
]

for stock in STOCKS:
    try:
        train_volatility(stock)
        train_anomaly_model(stock)
        print(f"[OK] Trained models for {stock}")
    except Exception as e:
        print(f"[ERROR] {stock}: {e}")

print("Startup complete!")