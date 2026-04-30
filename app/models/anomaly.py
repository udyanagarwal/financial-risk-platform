import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from dotenv import load_dotenv
import os
import pickle

load_dotenv()

def get_engine():
    DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    return create_engine(DB_URL)

def load_data(symbol):
    query = f"SELECT * FROM stock_prices WHERE symbol = '{symbol}' ORDER BY date"
    df = pd.read_sql(query, engine)
    return df

def calculate_features(df):
    """
    Calculate features that help detect anomalies
    """
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
    # StandardScaler makes all features have mean=0 and std=1
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Isolation Forest
    # contamination=0.05 means we expect ~5% of data to be anomalies
    model = IsolationForest(
        n_estimators=100,
        contamination=0.05,
        random_state=42
    )
    model.fit(X_scaled)
    
    # Detect anomalies on training data
    # -1 = anomaly, 1 = normal
    df['anomaly'] = model.predict(X_scaled)
    df['anomaly_score'] = model.score_samples(X_scaled)
    
    anomalies = df[df['anomaly'] == -1]
    print(f"[OK] Found {len(anomalies)} anomalies out of {len(df)} trading days")
    print(f"Anomaly dates for {symbol}:")
    print(anomalies[['date', 'close', 'daily_return', 'volume_ratio']].to_string())
    
    # Save model and scaler
    os.makedirs("app/models/saved", exist_ok=True)
    with open(f"app/models/saved/{symbol.replace('.', '_')}_anomaly.pkl", "wb") as f:
        pickle.dump({'model': model, 'scaler': scaler}, f)
    
    print(f"[OK] Anomaly model saved!")
    return model, scaler, anomalies

def detect_anomalies(symbol):
    """
    Detect if today's trading is anomalous
    """
    model_path = f"app/models/saved/{symbol.replace('.', '_')}_anomaly.pkl"
    with open(model_path, "rb") as f:
        saved = pickle.load(f)
    
    model = saved['model']
    scaler = saved['scaler']
    
    df = load_data(symbol)
    df = calculate_features(df)
    
    features = ['daily_return', 'volume_change', 'price_range',
                'volume_ratio', 'volatility_20']
    
    # Check only the latest trading day
    latest = df[features].iloc[-1].values.reshape(1, -1)
    latest_scaled = scaler.transform(latest)
    
    prediction = model.predict(latest_scaled)[0]
    score = model.score_samples(latest_scaled)[0]
    
    is_anomaly = prediction == -1
    
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