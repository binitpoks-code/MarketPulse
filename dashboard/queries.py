import pandas as pd
from datetime import date, timedelta
from sqlalchemy import func
from database.models import Quote, Article, SentimentScore, AnomalyAlert, PriceHistory, ForecastResult


def get_latest_quotes(session):
    subq = (
        session.query(Quote.ticker, func.max(Quote.fetched_at).label("max_ts"))
        .group_by(Quote.ticker)
        .subquery()
    )
    rows = (
        session.query(Quote)
        .join(subq, (Quote.ticker == subq.c.ticker) & (Quote.fetched_at == subq.c.max_ts))
        .all()
    )
    return pd.DataFrame([{
        "ticker": r.ticker,
        "current_price": r.current_price,
        "change": r.change,
        "percent_change": r.percent_change,
        "fetched_at": r.fetched_at,
    } for r in rows])


def get_latest_sentiment(session):
    subq = (
        session.query(SentimentScore.ticker, func.max(SentimentScore.scored_at).label("max_ts"))
        .group_by(SentimentScore.ticker)
        .subquery()
    )
    rows = (
        session.query(SentimentScore)
        .join(subq, (SentimentScore.ticker == subq.c.ticker) & (SentimentScore.scored_at == subq.c.max_ts))
        .all()
    )
    return pd.DataFrame([{
        "ticker": r.ticker,
        "score": r.score,
        "article_count": r.article_count,
        "scored_at": r.scored_at,
    } for r in rows])


def get_sentiment_history(session, ticker):
    rows = (
        session.query(SentimentScore)
        .filter(SentimentScore.ticker == ticker)
        .order_by(SentimentScore.scored_at)
        .all()
    )
    return pd.DataFrame([{
        "scored_at": r.scored_at,
        "score": r.score,
        "article_count": r.article_count,
    } for r in rows])


def get_anomaly_alerts(session):
    rows = (
        session.query(AnomalyAlert)
        .order_by(AnomalyAlert.detected_at.desc())
        .limit(50)
        .all()
    )
    return pd.DataFrame([{
        "ticker": r.ticker,
        "current_score": r.current_score,
        "baseline_mean": r.baseline_mean,
        "z_score": r.z_score,
        "detected_at": r.detected_at,
    } for r in rows])


def get_recent_articles(session, ticker, limit=25):
    rows = (
        session.query(Article)
        .filter(Article.ticker == ticker)
        .order_by(Article.published_at.desc())
        .limit(limit)
        .all()
    )
    return pd.DataFrame([{
        "headline": r.headline,
        "source_name": r.source_name,
        "published_at": r.published_at,
        "sentiment_compound": r.sentiment_compound,
        "url": r.url,
    } for r in rows])


def get_price_history(session, ticker, days=90):
    cutoff = date.today() - timedelta(days=days)
    rows = (
        session.query(PriceHistory)
        .filter(PriceHistory.ticker == ticker, PriceHistory.date >= cutoff)
        .order_by(PriceHistory.date)
        .all()
    )
    return pd.DataFrame([{
        "date": r.date,
        "close": r.close,
    } for r in rows])


def get_latest_forecast(session, ticker):
    subq = (
        session.query(func.max(ForecastResult.generated_at).label("max_ts"))
        .filter(ForecastResult.ticker == ticker)
        .subquery()
    )
    rows = (
        session.query(ForecastResult)
        .filter(ForecastResult.ticker == ticker, ForecastResult.generated_at == subq.c.max_ts)
        .order_by(ForecastResult.forecast_date)
        .all()
    )
    return pd.DataFrame([{
        "forecast_date": r.forecast_date,
        "predicted_close": r.predicted_close,
        "lower_bound": r.lower_bound,
        "upper_bound": r.upper_bound,
        "predicted_direction": r.predicted_direction,
        "directional_accuracy": r.directional_accuracy,
        "sentiment_contribution": r.sentiment_contribution,
        "price_contribution": r.price_contribution,
        "dow_contribution": r.dow_contribution,
        "generated_at": r.generated_at,
    } for r in rows])
