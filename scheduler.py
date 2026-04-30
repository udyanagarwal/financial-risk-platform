import schedule
import time
import subprocess
import sys
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

def log(message):
    """Print with timestamp"""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}")

def fetch_data():
    """Step 1 - Fetch latest stock data"""
    log("Starting daily data fetch...")
    try:
        result = subprocess.run(
            [sys.executable, "app/pipeline/fetch_data.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            log("Data fetch completed successfully!")
            log(result.stdout)
        else:
            log(f"Data fetch failed: {result.stderr}")
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
        
        log("All models retrained!")
    except Exception as e:
        log(f"Retraining failed: {e}")
    
    # Retrain anomaly models
    try:
        result = subprocess.run(
            [sys.executable, "app/models/anomaly.py"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            log("Anomaly models retrained successfully!")
        else:
            log(f"Anomaly retraining failed: {result.stderr}")
    except Exception as e:
        log(f"Error retraining anomaly: {e}")
    
    log("All models retrained! Predictions are now up to date.")

def daily_pipeline():
    """Run the full daily update pipeline"""
    log("=" * 50)
    log("STARTING DAILY PIPELINE")
    log("=" * 50)
    fetch_data()
    time.sleep(30)  # Wait 30 seconds between fetch and retrain
    retrain_models()
    log("=" * 50)
    log("DAILY PIPELINE COMPLETE")
    log("=" * 50)

# Schedule to run every day at 6:00 PM
# NSE market closes at 3:30 PM so 6 PM gives time for data to be available
schedule.every().day.at("18:00").do(daily_pipeline)

# Also schedule a quick data refresh at market open
schedule.every().day.at("09:30").do(fetch_data)

log("Scheduler started!")
log("Daily pipeline scheduled at 6:00 PM")
log("Data refresh scheduled at 9:30 AM")
log("Press Ctrl+C to stop")

# Run once immediately on startup
log("Running initial pipeline now...")
daily_pipeline()

# Keep running
while True:
    schedule.run_pending()
    time.sleep(60)  # Check every minute