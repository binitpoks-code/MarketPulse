import yfinance as yf
import time
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime
from logger import get_logger
from config import TICKERS

logger = get_logger("yahoo")

FETCH_TIMEOUT = 25  # seconds per ticker before giving up


def _fetch_ticker_history(ticker, period):
    """Fetch one ticker's history. Runs inside a thread so we can timeout it."""
    t = yf.Ticker(ticker)
    hist = t.history(period=period, auto_adjust=True)
    return hist


def fetch_ticker(ticker):
    try:
        with ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_fetch_ticker_history, ticker, "7d")
            try:
                hist = future.result(timeout=FETCH_TIMEOUT)
            except FuturesTimeoutError:
                logger.warning(f"{ticker}: timed out after {FETCH_TIMEOUT}s")
                return None

        if hist.empty:
            logger.warning(f"{ticker}: no price history returned")
            return None

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
            "price_history": price_history,
            "fetched_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"{ticker}: fetch failed - {e}")
        return None


def _fetch_one_history(ticker, period):
    """Fetch one ticker's full history as a list of dicts. Runs inside a thread."""
    t = yf.Ticker(ticker)
    hist = t.history(period=period, auto_adjust=True)
    if hist.empty:
        return ticker, []
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
    return ticker, rows


def fetch_history_all(tickers=None, period="1y"):
    tickers = tickers or TICKERS
    result = {}

    for ticker in tickers:
        with ThreadPoolExecutor(max_workers=1) as ex:
            future = ex.submit(_fetch_one_history, ticker, period)
            try:
                t, rows = future.result(timeout=FETCH_TIMEOUT)
                if rows:
                    result[t] = rows
                    logger.info(f"{t}: {len(rows)} days of history fetched")
                else:
                    logger.warning(f"{ticker}: no history rows returned")
            except FuturesTimeoutError:
                logger.warning(f"{ticker}: history fetch timed out after {FETCH_TIMEOUT}s, skipping")
            except Exception as e:
                logger.error(f"{ticker}: history fetch failed - {e}")

    return result


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
        time.sleep(1)

    return results
