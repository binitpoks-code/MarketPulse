import logging
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from prophet import Prophet
from sklearn.ensemble import RandomForestClassifier
import shap

from ingestion.yahoo import fetch_history_all
from database.models import PriceHistory, ForecastResult, SentimentScore
from config import TICKERS, FORECAST_HORIZON
from logger import get_logger

logging.getLogger("prophet").setLevel(logging.WARNING)
logging.getLogger("cmdstanpy").setLevel(logging.WARNING)

logger = get_logger("forecaster")

MIN_PROPHET = 30
MIN_SHAP = 20
BACKTEST_DAYS = 10
FORECAST_DAYS = FORECAST_HORIZON // 24 or 2


def load_price_from_db(session, ticker):
    rows = (
        session.query(PriceHistory)
        .filter(PriceHistory.ticker == ticker)
        .order_by(PriceHistory.date)
        .all()
    )
    return [
        {"ticker": r.ticker, "date": r.date.isoformat(), "open": r.open,
         "high": r.high, "low": r.low, "close": r.close, "volume": r.volume}
        for r in rows
    ]


def upsert_price_history(session, rows):
    if not rows:
        return
    ticker = rows[0]["ticker"]
    existing = {
        r.date
        for r in session.query(PriceHistory.date)
        .filter(PriceHistory.ticker == ticker)
        .all()
    }
    new_rows = [r for r in rows if pd.to_datetime(r["date"]).date() not in existing]
    for r in new_rows:
        session.add(PriceHistory(
            ticker=r["ticker"],
            date=pd.to_datetime(r["date"]).date(),
            open=r.get("open"),
            high=r.get("high"),
            low=r.get("low"),
            close=r["close"],
            volume=r.get("volume"),
        ))
    session.commit()
    if new_rows:
        logger.info(f"{ticker}: {len(new_rows)} new price rows saved")


def load_sentiment_map(session):
    rows = session.query(SentimentScore).all()
    result = {}
    for row in rows:
        if row.scored_at:
            result.setdefault(row.ticker, {})[row.scored_at.date()] = row.score
    return result


def build_model_df(price_rows, sentiment_by_date):
    df = pd.DataFrame(price_rows)
    df["ds"] = pd.to_datetime(df["date"])
    df["y"] = df["close"].astype(float)
    df = df[["ds", "y"]].sort_values("ds").reset_index(drop=True)
    # fill dates without sentiment with 0 (neutral baseline)
    df["sentiment"] = df["ds"].dt.date.map(sentiment_by_date).fillna(0).astype(float)
    return df


def compute_directional_accuracy(train, holdout, model):
    future_bt = model.make_future_dataframe(periods=len(holdout))
    sentiment_series = pd.concat([
        train.set_index("ds")["sentiment"],
        holdout.set_index("ds")["sentiment"],
    ])
    future_bt["sentiment"] = sentiment_series.reindex(future_bt["ds"]).fillna(0).values
    fc = model.predict(future_bt)
    preds = fc.tail(len(holdout))["yhat"].values
    actuals = holdout["y"].values
    baseline = float(train["y"].iloc[-1])
    pred_dirs = np.diff(np.concatenate([[baseline], preds])) > 0
    actual_dirs = np.diff(np.concatenate([[baseline], actuals])) > 0
    return round(float(np.mean(pred_dirs == actual_dirs)), 4)


def run_prophet(ticker, df):
    if len(df) < MIN_PROPHET:
        logger.warning(f"{ticker}: only {len(df)} rows, need {MIN_PROPHET} to run Prophet")
        return None, None

    directional_accuracy = None

    if len(df) > BACKTEST_DAYS + MIN_PROPHET:
        train = df.iloc[:-BACKTEST_DAYS].copy()
        holdout = df.iloc[-BACKTEST_DAYS:].copy()
        bt_model = Prophet(
            weekly_seasonality=True, yearly_seasonality=False,
            daily_seasonality=False, changepoint_prior_scale=0.05,
        )
        bt_model.add_regressor("sentiment")
        bt_model.fit(train)
        directional_accuracy = compute_directional_accuracy(train, holdout, bt_model)
        logger.info(f"{ticker}: directional accuracy={directional_accuracy}")

    last_sentiment = float(df["sentiment"].iloc[-1])
    model = Prophet(
        weekly_seasonality=True, yearly_seasonality=False,
        daily_seasonality=False, changepoint_prior_scale=0.05,
    )
    model.add_regressor("sentiment")
    model.fit(df)

    future = model.make_future_dataframe(periods=FORECAST_DAYS)
    future["sentiment"] = df.set_index("ds")["sentiment"].reindex(future["ds"]).fillna(last_sentiment).values
    fc = model.predict(future)

    last_close = float(df["y"].iloc[-1])
    results = []
    for _, row in fc.tail(FORECAST_DAYS).iterrows():
        direction = 1 if float(row["yhat"]) > last_close else 0
        results.append({
            "forecast_date": row["ds"].date(),
            "predicted_close": round(float(row["yhat"]), 4),
            "lower_bound": round(float(row["yhat_lower"]), 4),
            "upper_bound": round(float(row["yhat_upper"]), 4),
            "predicted_direction": direction,
            "directional_accuracy": directional_accuracy,
        })
        last_close = float(row["yhat"])

    return results, directional_accuracy


def compute_shap_contribution(ticker, df):
    if len(df) < MIN_SHAP:
        logger.info(f"{ticker}: not enough rows for SHAP ({len(df)}, need {MIN_SHAP})")
        return None, None, None

    df = df.copy()
    df["day_of_week"] = df["ds"].dt.dayofweek
    df["price_change_5d"] = df["y"].pct_change(5).fillna(0)
    df["direction"] = (df["y"].shift(-1) > df["y"]).astype(int)
    df = df.dropna()

    if len(df) < MIN_SHAP:
        return None, None, None

    features = ["sentiment", "price_change_5d", "day_of_week"]
    X = df[features].values
    y = df["direction"].values

    clf = RandomForestClassifier(n_estimators=100, random_state=42)
    clf.fit(X, y)

    explainer = shap.TreeExplainer(clf)
    shap_values = explainer.shap_values(X)
    if isinstance(shap_values, list):
        shap_arr = np.abs(shap_values[1])
    elif hasattr(shap_values, "ndim") and shap_values.ndim == 3:
        shap_arr = np.abs(shap_values[:, :, 1])
    else:
        shap_arr = np.abs(shap_values)

    importance = shap_arr.mean(axis=0)
    total = importance.sum()
    if total == 0:
        return None, None, None

    sentiment_c = round(float(importance[0] / total), 4)
    price_c = round(float(importance[1] / total), 4)
    dow_c = round(float(importance[2] / total), 4)

    logger.info(f"{ticker}: SHAP sentiment={sentiment_c} price={price_c} dow={dow_c}")
    return sentiment_c, price_c, dow_c


def run_forecasts(session):
    all_history = fetch_history_all()
    sentiment_map = load_sentiment_map(session)

    for ticker in TICKERS:
        price_rows = all_history.get(ticker) or load_price_from_db(session, ticker)

        if not price_rows:
            logger.warning(f"{ticker}: no price data available, skipping")
            continue

        upsert_price_history(session, price_rows)

        df = build_model_df(price_rows, sentiment_map.get(ticker, {}))
        forecast_rows, _ = run_prophet(ticker, df)

        if not forecast_rows:
            continue

        sentiment_c, price_c, dow_c = compute_shap_contribution(ticker, df)
        generated_at = datetime.now(timezone.utc)

        for r in forecast_rows:
            session.add(ForecastResult(
                ticker=ticker,
                forecast_date=r["forecast_date"],
                predicted_close=r["predicted_close"],
                lower_bound=r["lower_bound"],
                upper_bound=r["upper_bound"],
                predicted_direction=r["predicted_direction"],
                directional_accuracy=r["directional_accuracy"],
                sentiment_contribution=sentiment_c,
                price_contribution=price_c,
                dow_contribution=dow_c,
                generated_at=generated_at,
            ))

        session.commit()
        logger.info(f"{ticker}: forecast saved")
