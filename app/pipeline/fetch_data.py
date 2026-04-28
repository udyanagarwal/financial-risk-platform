import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

DB_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DB_URL)

STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS"
]

def fetch_and_store():
    print("Fetching stock data...")
    
    for symbol in STOCKS:
        try:
            stock = yf.download(symbol, period="1y", interval="1d", progress=False)
            
            # Fix for newer yfinance version
            stock.columns = ['open', 'high', 'low', 'close', 'volume']
            stock.reset_index(inplace=True)
            stock.columns = [str(c).lower() for c in stock.columns]
            stock["symbol"] = symbol
            
            stock.to_sql("stock_prices", engine, if_exists="append", index=False)
            print(f"[OK] Stored data for {symbol}")
        
        except Exception as e:
            print(f"[ERROR] fetching {symbol}: {e}")

if __name__ == "__main__":
    fetch_and_store()