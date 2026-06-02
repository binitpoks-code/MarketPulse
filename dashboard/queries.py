import pandas as pd
from sqlalchemy import text


def _read(engine, sql, params=None):
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        return pd.DataFrame(result.fetchall(), columns=result.keys())


def get_latest_quotes(engine):
    return _read(engine, """
        SELECT q.ticker, q.current_price, q.change, q.percent_change, q.fetched_at
        FROM quotes q
        JOIN (SELECT ticker, MAX(fetched_at) AS max_ts FROM quotes GROUP BY ticker) sub
        ON q.ticker = sub.ticker AND q.fetched_at = sub.max_ts
    """)


def get_latest_sentiment(engine):
    return _read(engine, """
        SELECT s.ticker, s.score, s.article_count, s.scored_at
        FROM sentiment_scores s
        JOIN (SELECT ticker, MAX(scored_at) AS max_ts FROM sentiment_scores GROUP BY ticker) sub
        ON s.ticker = sub.ticker AND s.scored_at = sub.max_ts
    """)


def get_sentiment_history(engine, ticker):
    return _read(engine, """
        SELECT scored_at, score, article_count
        FROM sentiment_scores
        WHERE ticker = :ticker
        ORDER BY scored_at
    """, params={"ticker": ticker})


def get_anomaly_alerts(engine):
    return _read(engine, """
        SELECT ticker, current_score, baseline_mean, z_score, detected_at
        FROM anomaly_alerts
        ORDER BY detected_at DESC
        LIMIT 50
    """)


def get_recent_articles(engine, ticker, limit=25):
    return _read(engine, """
        SELECT headline, source_name, published_at, sentiment_compound, url
        FROM articles
        WHERE ticker = :ticker
        ORDER BY published_at DESC
        LIMIT :limit
    """, params={"ticker": ticker, "limit": limit})


def get_price_history(engine, ticker, days=90):
    return _read(engine, """
        SELECT date, close
        FROM price_history
        WHERE ticker = :ticker
          AND date >= CURRENT_DATE - :days * INTERVAL '1 day'
        ORDER BY date
    """, params={"ticker": ticker, "days": days})


def get_latest_forecast(engine, ticker):
    return _read(engine, """
        SELECT f.forecast_date, f.predicted_close, f.lower_bound, f.upper_bound,
               f.predicted_direction, f.directional_accuracy,
               f.sentiment_contribution, f.price_contribution, f.dow_contribution,
               f.generated_at
        FROM forecast_results f
        JOIN (SELECT MAX(generated_at) AS max_ts FROM forecast_results WHERE ticker = :ticker) sub
        ON f.generated_at = sub.max_ts
        WHERE f.ticker = :ticker
        ORDER BY f.forecast_date
    """, params={"ticker": ticker})
