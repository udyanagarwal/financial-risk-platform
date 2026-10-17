import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from dotenv import load_dotenv
import os
import pickle
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.db import get_engine

load_dotenv()

SAVED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saved")

def load_data(symbol):
    engine = get_engine()
    query = f"SELECT * FROM stock_prices WHERE symbol = '{symbol}' ORDER BY date"
    df = pd.read_sql(query, engine)
    if df.empty:
        raise ValueError(f"No stock data found in database for {symbol}. Run data fetch pipeline first.")
    print(f"Loaded {len(df)} rows for {symbol}")
    return df

def calculate_features(df):
    """
    Calculate features that help detect anomalies
    """
    df = df.copy()
    # Daily return
    df['daily_return'] = df['close'].pct_change()
    
    # Volume change — sudden spikes in volume are suspicious
    df['volume_change'] = df['volume'].pct_change()
    
    # Price range — unusually large ranges signal anomalies
    df['price_range'] = (df['high'] - df['low']) / df['close']
    
    # Rolling averages to compare against
    df['avg_volume_20'] = df['volume'].rolling(window=20).mean()
    df['volume_ratio'] = df['volume'] / df['avg_volume_20']
    
    df['volatility_20'] = df['daily_return'].rolling(window=20).std()
    # Replace infinity values with NaN then drop them
    df.replace([np.inf, -np.inf], np.nan, inplace=True)
    
    df.dropna(inplace=True)
    return df

def train_anomaly_model(symbol="TCS.NS"):
    """
    Train Isolation Forest to detect anomalies
    """
    print(f"Training anomaly detection model for {symbol}...")
    
    df = load_data(symbol)
    df = calculate_features(df)
    
    features = ['daily_return', 'volume_change', 'price_range', 
                'volume_ratio', 'volatility_20']
    
    X = df[features]
    
    # Scale features — important for anomaly detection
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Isolation Forest
    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42
    )
    model.fit(X_scaled)
    
    df['anomaly'] = model.predict(X_scaled)
    df['anomaly_score'] = model.score_samples(X_scaled)
    
    anomalies = df[df['anomaly'] == -1]
    print(f"[OK] Found {len(anomalies)} anomalies out of {len(df)} trading days")
    
    # Save model and scaler
    os.makedirs(SAVED_DIR, exist_ok=True)
    model_path = os.path.join(SAVED_DIR, f"{symbol.replace('.', '_')}_anomaly.pkl")
    with open(model_path, "wb") as f:
        pickle.dump({'model': model, 'scaler': scaler}, f)
    
    print(f"[OK] Anomaly model saved to {model_path}!")
    return model, scaler, anomalies

def detect_anomalies(symbol, model=None, scaler=None, df=None):
    """
    Detect if today's trading is anomalous
    """
    if model is None or scaler is None:
        model_path = os.path.join(SAVED_DIR, f"{symbol.replace('.', '_')}_anomaly.pkl")
        if not os.path.exists(model_path):
            print(f"Anomaly model not found at {model_path}, training new model...")
            model, scaler, _ = train_anomaly_model(symbol)
        else:
            with open(model_path, "rb") as f:
                saved = pickle.load(f)
            model = saved['model']
            scaler = saved['scaler']
    
    if df is None or df.empty:
        df = load_data(symbol)
    else:
        df = df.copy()
        
    df = calculate_features(df)
    
    features = ['daily_return', 'volume_change', 'price_range',
                'volume_ratio', 'volatility_20']
    
    # Check only the latest trading day
    latest = df[features].iloc[[-1]]
    latest_scaled = scaler.transform(latest)
    
    prediction = model.predict(latest_scaled)[0]
    score = model.score_samples(latest_scaled)[0]
    
    is_anomaly = bool(prediction == -1)
    
    return {
        "symbol": symbol,
        "is_anomaly": is_anomaly,
        "anomaly_score": round(float(score), 4),
        "date": str(df['date'].iloc[-1])
    }

if __name__ == "__main__":
    STOCKS = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS"
    ]
    
    for stock in STOCKS:
        train_anomaly_model(stock)
        result = detect_anomalies(stock)
        print(f"\nLatest day check -> {result}")
        print("=" * 50)