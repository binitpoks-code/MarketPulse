import json
import pandas as pd
from logger import get_logger

logger = get_logger("processing")


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def process_quotes(raw_path="data/raw/finnhub_quotes.json"):
    data = load_json(raw_path)
    if not data:
        logger.warning("quotes file is empty")
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df = df.drop(columns=["source"], errors="ignore")

    numeric_cols = ["current_price", "change", "percent_change", "high", "low", "open", "prev_close"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(subset=["current_price"])
    df["fetched_at"] = pd.to_datetime(df["fetched_at"])

    logger.info(f"quotes: {len(df)} rows processed")
    return df


def process_articles(
    finnhub_path="data/raw/finnhub_news.json",
    news_api_path="data/raw/news.json",
):
    finnhub_raw = load_json(finnhub_path)
    news_raw = load_json(news_api_path)

    rows = []

    for item in finnhub_raw:
        rows.append({
            "source_type": "finnhub_news",
            "ticker": item.get("ticker"),
            "headline": item.get("headline", "").strip(),
            "body": item.get("summary", "").strip(),
            "url": item.get("url", ""),
            "source_name": item.get("source_name", ""),
            "published_at": item.get("published_at"),
            "fetched_at": item.get("fetched_at"),
        })

    for item in news_raw:
        # prefer description over content since content is often truncated
        body = item.get("description") or item.get("content") or ""
        rows.append({
            "source_type": "news_api",
            "ticker": None,
            "headline": item.get("title", "").strip(),
            "body": body.strip(),
            "url": item.get("url", ""),
            "source_name": item.get("source_name", ""),
            "published_at": item.get("published_at"),
            "fetched_at": item.get("fetched_at"),
        })

    df = pd.DataFrame(rows)

    df = df[df["headline"].str.len() > 0]
    df = df[df["body"].str.len() > 0]
    df = df.drop_duplicates(subset=["url"])

    df["published_at"] = pd.to_datetime(df["published_at"], utc=True, errors="coerce")
    df["fetched_at"] = pd.to_datetime(df["fetched_at"], errors="coerce")

    df = df.sort_values("published_at", ascending=False).reset_index(drop=True)

    counts = df["source_type"].value_counts().to_dict()
    logger.info(f"articles: {len(df)} rows processed {counts}")
    return df


def process_prices(yahoo_path="data/raw/yahoo.json"):
    data = load_json(yahoo_path)
    if not data:
        logger.warning("yahoo prices file is empty, skipping")
        return pd.DataFrame()

    rows = []
    for stock in data:
        ticker = stock.get("ticker")
        for day in stock.get("price_history", []):
            rows.append({
                "ticker": ticker,
                "date": day.get("date"),
                "open": day.get("open"),
                "high": day.get("high"),
                "low": day.get("low"),
                "close": day.get("close"),
                "volume": day.get("volume"),
            })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["ticker", "date"]).reset_index(drop=True)

    logger.info(f"prices: {len(df)} rows across {df['ticker'].nunique()} tickers")
    return df
