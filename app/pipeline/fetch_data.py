import yfinance as yf
import pandas as pd
from sqlalchemy import text
from dotenv import load_dotenv
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from app.db import get_engine

load_dotenv()

STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS"
]

def fetch_and_store():
    engine = get_engine()
    print("Connecting to database and fetching stock data from Yahoo Finance...")
    
    for symbol in STOCKS:
        try:
            stock = yf.download(symbol, period="1y", interval="1d", progress=False)
            if stock.empty:
                print(f"[WARN] No data fetched for {symbol}")
                continue
            
            # Extract standard OHLCV columns (handle possible MultiIndex from yfinance)
            if isinstance(stock.columns, pd.MultiIndex):
                stock = stock.droplevel(1, axis=1) if stock.columns.nlevels > 1 else stock
                
            stock = stock[['Open', 'High', 'Low', 'Close', 'Volume']].copy()
            stock.reset_index(inplace=True)
            stock.columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            stock["symbol"] = symbol
            
            with engine.begin() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS stock_prices (
                        date TIMESTAMP,
                        open FLOAT,
                        high FLOAT,
                        low FLOAT,
                        close FLOAT,
                        volume BIGINT,
                        symbol TEXT
                    )
                """))
                conn.execute(text(f"DELETE FROM stock_prices WHERE symbol = '{symbol}'"))
                stock.to_sql("stock_prices", conn, if_exists="append", index=False)
            
            with engine.connect() as conn:
                result = conn.execute(text(f"SELECT COUNT(*) FROM stock_prices WHERE symbol = '{symbol}'"))
                count = result.fetchone()[0]
                print(f"[OK] Stored {count} rows for {symbol}")
        
        except Exception as e:
            print(f"[ERROR] fetching {symbol}: {e}")

if __name__ == "__main__":
    fetch_and_store()