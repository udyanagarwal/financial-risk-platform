import schedule
import time
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def log(message):
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def fetch_data():
    log("Starting daily data fetch...")
    try:
        from app.pipeline.fetch_data import fetch_and_store
        fetch_and_store()
        log("Data fetch completed successfully!")
    except Exception as e:
        log(f"Error in fetch_data: {e}")

def retrain_models():
    log("Starting model retraining...")
    try:
        from app.models.volatility import train_model
        from app.models.anomaly import train_anomaly_model
        
        STOCKS = [
            "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
            "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS"
        ]
        
        for stock in STOCKS:
            try:
                train_model(stock)
                train_anomaly_model(stock)
                log(f"[OK] Retrained models for {stock}")
            except Exception as e:
                log(f"[ERROR] Retraining {stock}: {e}")
        
        log("All models retrained! Predictions are now up to date.")
    except Exception as e:
        log(f"Retraining failed: {e}")

def daily_pipeline():
    log("=" * 50)
    log("STARTING DAILY PIPELINE")
    log("=" * 50)
    fetch_data()
    time.sleep(60)
    retrain_models()
    log("=" * 50)
    log("DAILY PIPELINE COMPLETE")
    log("=" * 50)

schedule.every().day.at("18:00").do(daily_pipeline)
schedule.every().day.at("09:30").do(fetch_data)

log("Scheduler started!")
log("Daily pipeline scheduled at 6:00 PM")
log("Data refresh scheduled at 9:30 AM")
log("Press Ctrl+C to stop")
log("Running initial pipeline now...")
daily_pipeline()

while True:
    schedule.run_pending()
    time.sleep(60)