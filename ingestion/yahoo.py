import yfinance as yf
import time
from datetime import datetime
from logger import get_logger
from config import TICKERS

logger = get_logger("yahoo")


def fetch_ticker(ticker):
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="7d")

        if hist.empty:
            logger.warning(f"{ticker}: no price history returned")
            return None

        info = {}
        try:
            info = t.info
        except Exception:
            logger.warning(f"{ticker}: could not fetch info, using price history only")

        price_history = []
        for date, row in hist.iterrows():
            price_history.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 4),
                "high": round(float(row["High"]), 4),
                "low": round(float(row["Low"]), 4),
                "close": round(float(row["Close"]), 4),
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


def fetch_history_all(tickers=None, period="1y"):
    tickers = tickers or TICKERS
    try:
        raw = yf.download(" ".join(tickers), period=period, auto_adjust=True, progress=False, group_by="ticker")

        if raw.empty:
            logger.warning("batch history download returned empty data")
            return {}

        result = {}
        for ticker in tickers:
            try:
                hist = raw[ticker] if len(tickers) > 1 else raw
                rows = []
                for date, row in hist.iterrows():
                    rows.append({
                        "ticker": ticker,
                        "date": date.strftime("%Y-%m-%d"),
                        "open": round(float(row["Open"]), 4),
                        "high": round(float(row["High"]), 4),
                        "low": round(float(row["Low"]), 4),
                        "close": round(float(row["Close"]), 4),
                        "volume": int(row["Volume"]),
                    })
                result[ticker] = rows
                logger.info(f"{ticker}: {len(rows)} days of history fetched")
            except Exception as e:
                logger.error(f"{ticker}: failed to parse history - {e}")

        return result

    except Exception as e:
        logger.error(f"batch history fetch failed - {e}")
        return {}


def fetch_all(tickers=None):
    tickers = tickers or TICKERS
    results = []

    for ticker in tickers:
        data = fetch_ticker(ticker)
        if data:
            results.append(data)
            logger.info(f"{ticker}: fetched successfully")
        else:
            logger.warning(f"{ticker}: skipped, no data returned")
        time.sleep(3)

    return results
