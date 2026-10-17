import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

def get_db_url():
    """
    Get PostgreSQL database URL supporting both single DATABASE_URL
    (standard on Neon, Render, Railway, Supabase) and split DB_* variables.
    Ensures SSL mode is properly enabled for cloud databases.
    """
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        # SQLAlchemy requires postgresql:// instead of postgres://
        if db_url.startswith("postgres://"):
            db_url = "postgresql://" + db_url[len("postgres://"):]
        if "sslmode=" not in db_url and "localhost" not in db_url and "127.0.0.1" not in db_url:
            separator = "&" if "?" in db_url else "?"
            db_url += f"{separator}sslmode=require"
        return db_url

    user = os.getenv("DB_USER", "")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "")

    ssl = ""
    if host and "localhost" not in host and "127.0.0.1" not in host:
        ssl = "?sslmode=require"

    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}{ssl}"

def get_engine():
    """
    Creates an SQLAlchemy engine with pre-ping enabled to automatically
    reconnect if serverless Postgres (like Neon) temporarily sleeps.
    """
    return create_engine(get_db_url(), pool_pre_ping=True)
