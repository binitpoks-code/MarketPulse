import requests
import time
from datetime import datetime
from logger import get_logger
from config import TICKERS

logger = get_logger("stocktwits")

BASE_URL = "https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"


def fetch_ticker(ticker):
    url = BASE_URL.format(ticker=ticker)
    try:
        response = requests.get(url, timeout=10)

        if response.status_code == 200:
            data = response.json()
            messages = data.get("messages", [])
            posts = []
            for msg in messages:
                sentiment = None
                if msg.get("entities", {}).get("sentiment"):
                    sentiment = msg["entities"]["sentiment"].get("basic")

                posts.append({
                    "source": "stocktwits",
                    "ticker": ticker,
                    "id": str(msg.get("id")),
                    "text": msg.get("body", ""),
                    "user": msg.get("user", {}).get("username", ""),
                    "likes": msg.get("likes", {}).get("total", 0),
                    "sentiment_label": sentiment,
                    "created_at": msg.get("created_at"),
                    "fetched_at": datetime.utcnow().isoformat(),
                })
            return posts

        elif response.status_code == 429:
            logger.warning(f"{ticker}: rate limited, waiting 60s")
            time.sleep(60)
            return []
        else:
            logger.warning(f"{ticker}: got status {response.status_code}")
            return []

    except Exception as e:
        logger.error(f"{ticker}: request failed - {e}")
        return []


def fetch_all(tickers=None):
    tickers = tickers or TICKERS
    all_posts = []

    for ticker in tickers:
        posts = fetch_ticker(ticker)
        all_posts.extend(posts)
        logger.info(f"{ticker}: {len(posts)} posts fetched")
        time.sleep(0.5)

    return all_posts
