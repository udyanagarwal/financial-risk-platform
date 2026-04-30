import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from dotenv import load_dotenv
import os
import pickle

load_dotenv()

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)

def load_data(symbol):
    query = f"SELECT * FROM stock_prices WHERE symbol = '{symbol}' ORDER BY date"
    df = pd.read_sql(query, engine)
    print(f"Loaded {len(df)} rows for {symbol}")
    return df

def calculate_features(df):
    """
    Calculate technical features for ML model.
    These are the inputs our model will learn from.
    """
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
    # 80% for training, 20% for testing
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )
    
    # Train Random Forest model
    # Why Random Forest? It handles non-linear patterns well
    # and is more powerful than Linear Regression
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate model
    predictions = model.predict(X_test)
    mse = mean_squared_error(y_test, predictions)
    rmse = np.sqrt(mse)
    print(f"Model RMSE: {rmse:.6f}")
    
    # Save model to disk so API can use it later
    os.makedirs("app/models/saved", exist_ok=True)
    with open(f"app/models/saved/{symbol.replace('.', '_')}_volatility.pkl", "wb") as f:
        pickle.dump(model, f)
    print(f"[OK] Model saved!")
    
    return model, rmse

def predict_volatility(symbol, model=None):
    """
    Predict tomorrow's volatility for a given stock
    """
    if model is None:
        # Load saved model
        model_path = f"app/models/saved/{symbol.replace('.', '_')}_volatility.pkl"
        with open(model_path, "rb") as f:
            model = pickle.load(f)
    
    df = load_data(symbol)
    df = calculate_features(df)
    
    features = ['ma_7', 'ma_21', 'vol_7', 'price_range',
                'return_lag1', 'return_lag2', 'return_lag3']
    
    # Use the most recent row to predict tomorrow
    latest = df[features].iloc[-1].values.reshape(1, -1)
    prediction = model.predict(latest)[0]
    
    return round(prediction, 6)

if __name__ == "__main__":
    # Train model for all stocks
    STOCKS = [
        "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
        "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS"
    ]
    
    for stock in STOCKS:
        model, rmse = train_model(stock)
        prediction = predict_volatility(stock, model)
        print(f"{stock} -> Predicted volatility: {prediction}")
        print("-" * 40)