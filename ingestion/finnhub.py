import requests
import time
from datetime import datetime, timedelta
from logger import get_logger
from config import FINNHUB_API_KEY, TICKERS

logger = get_logger("finnhub")

BASE_URL = "https://finnhub.io/api/v1"


def fetch_quote(ticker):
    url = f"{BASE_URL}/quote"
    params = {"symbol": ticker, "token": FINNHUB_API_KEY}
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            d = response.json()
            return {
                "source": "finnhub_quote",
                "ticker": ticker,
                "current_price": d.get("c"),
                "change": d.get("d"),
                "percent_change": d.get("dp"),
                "high": d.get("h"),
                "low": d.get("l"),
                "open": d.get("o"),
                "prev_close": d.get("pc"),
                "fetched_at": datetime.utcnow().isoformat(),
            }
        else:
            logger.warning(f"{ticker}: quote returned {response.status_code}")
            return None
    except Exception as e:
        logger.error(f"{ticker}: quote failed - {e}")
        return None


def fetch_company_news(ticker, days_back=2):
    url = f"{BASE_URL}/company-news"
    to_date = datetime.utcnow().strftime("%Y-%m-%d")
    from_date = (datetime.utcnow() - timedelta(days=days_back)).strftime("%Y-%m-%d")
    params = {
        "symbol": ticker,
        "from": from_date,
        "to": to_date,
        "token": FINNHUB_API_KEY,
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            articles = response.json()
            results = []
            for article in articles[:15]:
                results.append({
                    "source": "finnhub_news",
                    "ticker": ticker,
                    "headline": article.get("headline", ""),
                    "summary": article.get("summary", ""),
                    "url": article.get("url", ""),
                    "source_name": article.get("source", ""),
                    "published_at": datetime.utcfromtimestamp(article.get("datetime", 0)).isoformat(),
                    "fetched_at": datetime.utcnow().isoformat(),
                })
            return results
        else:
            logger.warning(f"{ticker}: company news returned {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"{ticker}: company news failed - {e}")
        return []


def fetch_all(tickers=None):
    tickers = tickers or TICKERS
    quotes = []
    all_news = []

    for ticker in tickers:
        quote = fetch_quote(ticker)
        if quote:
            quotes.append(quote)
            logger.info(f"{ticker}: quote fetched at ${quote.get('current_price')}")

        news = fetch_company_news(ticker)
        all_news.extend(news)
        logger.info(f"{ticker}: {len(news)} company news articles fetched")

        time.sleep(0.5)

    return {"quotes": quotes, "news": all_news}
