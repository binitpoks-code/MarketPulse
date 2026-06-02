import os
from dotenv import load_dotenv

load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "marketpulse")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

KAFKA_BOOTSTRAP_SERVERS = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

TICKERS = ["AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN", "META", "SPY"]

NEWS_QUERIES = ["stock market", "S&P 500", "NASDAQ", "earnings report", "tech stocks"]

SENTIMENT_WINDOW = 24
ANOMALY_THRESHOLD = 2.0
FORECAST_HORIZON = 48
