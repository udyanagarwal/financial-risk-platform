import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
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
    Calculate technical features for ML model.
    These are the inputs our model will learn from.
    """
    df = df.copy()
    # Daily return = (today's close - yesterday's close) / yesterday's close
    df['daily_return'] = df['close'].pct_change()
    
    # Volatility = standard deviation of returns over last 20 days
    # This is our TARGET variable — what we want to predict
    df['volatility'] = df['daily_return'].rolling(window=20).std()
    
    # Features — what the model uses to make predictions
    df['ma_7'] = df['close'].rolling(window=7).mean()   # 7-day moving average
    df['ma_21'] = df['close'].rolling(window=21).mean() # 21-day moving average
    df['vol_7'] = df['daily_return'].rolling(window=7).std()  # 7-day volatility
    df['price_range'] = (df['high'] - df['low']) / df['close']  # daily price range
    df['return_lag1'] = df['daily_return'].shift(1)  # yesterday's return
    df['return_lag2'] = df['daily_return'].shift(2)  # 2 days ago return
    df['return_lag3'] = df['daily_return'].shift(3)  # 3 days ago return
    
    # Drop rows with missing values (from rolling calculations)
    df.dropna(inplace=True)
    
    return df

def train_model(symbol="TCS.NS"):
    """
    Train a Random Forest model to predict volatility
    """
    print(f"Training volatility model for {symbol}...")
    
    # Load and prepare data
    df = load_data(symbol)
    df = calculate_features(df)
    
    # Define features (X) and target (y)
    features = ['ma_7', 'ma_21', 'vol_7', 'price_range', 
                'return_lag1', 'return_lag2', 'return_lag3']
    
    X = df[features]
    y = df['volatility']
    
    # Split into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )
    
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate model
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    rmse = np.sqrt(mse)
    print(f"Model RMSE: {rmse:.6f}")
    
    # Save model to disk so API can use it later
    os.makedirs(SAVED_DIR, exist_ok=True)
    model_path = os.path.join(SAVED_DIR, f"{symbol.replace('.', '_')}_volatility.pkl")
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"[OK] Model saved to {model_path}!")
    
    return model, rmse

def predict_volatility(symbol, model=None, df=None):
    """
    Predict tomorrow's volatility for a given stock
    """
    if model is None:
        model_path = os.path.join(SAVED_DIR, f"{symbol.replace('.', '_')}_volatility.pkl")
        if not os.path.exists(model_path):
            print(f"Model not found at {model_path}, training new model...")
            model, _ = train_model(symbol)
        else:
            with open(model_path, "rb") as f:
                model = pickle.load(f)
    
    if df is None or df.empty:
        df = load_data(symbol)
    else:
        df = df.copy()
        
    df = calculate_features(df)
    
    features = ['ma_7', 'ma_21', 'vol_7', 'price_range',
                'return_lag1', 'return_lag2', 'return_lag3']
    
    # Use the most recent row to predict tomorrow
    latest = df[features].iloc[[-1]]
    prediction = float(model.predict(latest)[0])
    
    return round(prediction, 6)

if __name__ == "__main__":
    STOCKS = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS"
    ]
    
    for stock in STOCKS:
        model, rmse = train_model(stock)
        prediction = predict_volatility(stock, model)
        print(f"{stock} -> Predicted volatility: {prediction}")
        print("-" * 40)