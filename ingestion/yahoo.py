import yfinance as yf
from datetime import datetime
from logger import get_logger
from config import TICKERS

logger = get_logger("yahoo")


def fetch_ticker(ticker):
    try:
        t = yf.Ticker(ticker)
        info = t.info
        hist = t.history(period="7d")

        price_history = []
        for date, row in hist.iterrows():
            price_history.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(row["Open"], 4),
                "high": round(row["High"], 4),
                "low": round(row["Low"], 4),
                "close": round(row["Close"], 4),
                "volume": int(row["Volume"]),
            })

        return {
            "source": "yahoo_finance",
            "ticker": ticker,
            "name": info.get("longName", ticker),
            "current_price": info.get("currentPrice") or info.get("regularMarketPrice"),
            "market_cap": info.get("marketCap"),
            "sector": info.get("sector"),
            "pe_ratio": info.get("trailingPE"),
            "fifty_two_week_high": info.get("fiftyTwoWeekHigh"),
            "fifty_two_week_low": info.get("fiftyTwoWeekLow"),
            "price_history": price_history,
            "fetched_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"{ticker}: fetch failed - {e}")
        return None


def fetch_all(tickers=None):
    tickers = tickers or TICKERS
    results = []

    for ticker in tickers:
        data = fetch_ticker(ticker)
        if data:
            results.append(data)
            logger.info(f"{ticker}: fetched at ${data.get('current_price')}")

    return results
