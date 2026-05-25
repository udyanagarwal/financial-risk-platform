import yfinance as yf
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

load_dotenv()

STOCKS = [
    "RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
    "HINDUNILVR.NS", "SBIN.NS", "BHARTIARTL.NS", "ITC.NS", "KOTAKBANK.NS"
]

def get_engine():
    DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}?sslmode=require"
    return create_engine(DB_URL)

def fetch_and_store():
    engine = get_engine()
    print(f"Connecting to: {os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}")
    print("Fetching stock data...")
    
    for symbol in STOCKS:
        try:
            stock = yf.download(symbol, period="1y", interval="1d", progress=False)
            stock = stock.iloc[:, :5]
            stock.columns = ['open', 'high', 'low', 'close', 'volume']
            stock.reset_index(inplace=True)
            stock.columns = [str(c).lower() for c in stock.columns]
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