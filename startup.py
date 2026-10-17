import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models.volatility import train_model as train_volatility, SAVED_DIR
from app.models.anomaly import train_anomaly_model

print("Running startup check - validating ML models...")

STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS"
]

for stock in STOCKS:
    vol_file = os.path.join(SAVED_DIR, f"{stock.replace('.', '_')}_volatility.pkl")
    anom_file = os.path.join(SAVED_DIR, f"{stock.replace('.', '_')}_anomaly.pkl")
    
    need_training = not os.path.exists(vol_file) or not os.path.exists(anom_file)
    if need_training:
        try:
            print(f"Training missing models for {stock}...")
            train_volatility(stock)
            train_anomaly_model(stock)
            print(f"[OK] Trained models for {stock}")
        except Exception as e:
            print(f"[ERROR] Training {stock}: {e}")
    else:
        print(f"[OK] Models verified for {stock}")

print("Startup check complete! Ready to serve traffic.")