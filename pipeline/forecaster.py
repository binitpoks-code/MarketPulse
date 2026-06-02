import logging
import time
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from prophet import Prophet
from ingestion.yahoo import fetch_history_all
from database.models import PriceHistory, ForecastResult
from config import TICKERS, FORECAST_HORIZON
from logger import get_logger

logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)

logger = get_logger("forecaster")

MIN_ROWS = 30
BACKTEST_DAYS = 10
FORECAST_DAYS = FORECAST_HORIZON // 24 or 2


def upsert_price_history(session, rows):
    existing = {
        (r.ticker, r.date)
        for r in session.query(PriceHistory.ticker, PriceHistory.date).all()
    }

    new_rows = [r for r in rows if (r["ticker"], pd.to_datetime(r["date"]).date()) not in existing]

    for r in new_rows:
        session.add(PriceHistory(
            ticker=r["ticker"],
            date=pd.to_datetime(r["date"]).date(),
            open=r["open"],
            high=r["high"],
            low=r["low"],
            close=r["close"],
            volume=r["volume"],
        ))

    session.commit()
    logger.info(f"{new_rows[0]['ticker'] if new_rows else 'unknown'}: {len(new_rows)} new price rows inserted")
    return new_rows


def build_forecast(ticker, rows):
    df = pd.DataFrame(rows)
    df["ds"] = pd.to_datetime(df["date"])
    df["y"] = df["close"].astype(float)
    df = df[["ds", "y"]].sort_values("ds").reset_index(drop=True)

    if len(df) < MIN_ROWS:
        logger.warning(f"{ticker}: only {len(df)} rows, need {MIN_ROWS} for forecasting")
        return []

    # backtest on holdout to compute MAE
    train = df.iloc[:-BACKTEST_DAYS]
    holdout = df.iloc[-BACKTEST_DAYS:]

    backtest_model = Prophet(
        weekly_seasonality=True,
        yearly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
    )
    backtest_model.fit(train)

    future_bt = backtest_model.make_future_dataframe(periods=BACKTEST_DAYS)
    forecast_bt = backtest_model.predict(future_bt)
    predicted = forecast_bt.tail(BACKTEST_DAYS)["yhat"].values
    actual = holdout["y"].values
    mae = float(np.mean(np.abs(predicted - actual)))

    # full model on all data for the real forecast
    full_model = Prophet(
        weekly_seasonality=True,
        yearly_seasonality=True,
        daily_seasonality=False,
        changepoint_prior_scale=0.05,
    )
    full_model.fit(df)

    future = full_model.make_future_dataframe(periods=FORECAST_DAYS)
    forecast = full_model.predict(future)

    generated_at = datetime.now(timezone.utc)
    results = []
    for _, row in forecast.tail(FORECAST_DAYS).iterrows():
        results.append(ForecastResult(
            ticker=ticker,
            forecast_date=row["ds"].date(),
            predicted_close=round(float(row["yhat"]), 4),
            lower_bound=round(float(row["yhat_lower"]), 4),
            upper_bound=round(float(row["yhat_upper"]), 4),
            mae=round(mae, 4),
            generated_at=generated_at,
        ))

    logger.info(f"{ticker}: MAE={mae:.4f}, forecasting {FORECAST_DAYS} days ahead")
    return results


def run_forecasts(session):
    all_history = fetch_history_all()

    if not all_history:
        logger.error("no price history returned, aborting forecasting")
        return

    for ticker, rows in all_history.items():
        if not rows:
            logger.warning(f"{ticker}: no history available, skipping")
            continue

        upsert_price_history(session, rows)

        results = build_forecast(ticker, rows)
        if not results:
            continue

        for result in results:
            session.add(result)

        session.commit()
        logger.info(f"{ticker}: forecast saved")
