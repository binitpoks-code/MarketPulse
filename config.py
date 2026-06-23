import os
from dotenv import load_dotenv

load_dotenv()


def _get(key, default=""):
    try:
        import streamlit as st
        val = st.secrets.get(key)
        if val is not None:
            return val
    except Exception:
        pass
    return os.getenv(key, default)


NEWS_API_KEY = _get("NEWS_API_KEY")
FINNHUB_API_KEY = _get("FINNHUB_API_KEY")

DB_HOST = _get("DB_HOST", "localhost")
DB_PORT = _get("DB_PORT", "5432")
DB_NAME = _get("DB_NAME", "marketpulse")
DB_USER = _get("DB_USER", "postgres")
DB_PASSWORD = _get("DB_PASSWORD", "")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

KAFKA_BOOTSTRAP_SERVERS = _get("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

TICKERS = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "SPY"]

NEWS_QUERIES = ["stock market", "S&P 500", "NASDAQ", "earnings report", "tech stocks"]

SENTIMENT_WINDOW = 24
ANOMALY_THRESHOLD = 2.0
FORECAST_HORIZON = 48
