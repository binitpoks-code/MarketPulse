import numpy as np
from datetime import datetime, timezone
from database.models import SentimentScore, AnomalyAlert
from config import TICKERS, ANOMALY_THRESHOLD
from logger import get_logger

logger = get_logger("anomaly")

# minimum number of historical data points needed to compute a reliable baseline
MIN_HISTORY = 3


def detect_anomalies(session):
    alerts = []

    for ticker in TICKERS:
        scores = (
            session.query(SentimentScore)
            .filter(SentimentScore.ticker == ticker)
            .order_by(SentimentScore.scored_at)
            .all()
        )

        if len(scores) < MIN_HISTORY:
            logger.info(f"{ticker}: not enough history ({len(scores)} points, need {MIN_HISTORY})")
            continue

        historical = np.array([s.score for s in scores[:-1]])
        current = scores[-1].score

        mean = float(np.mean(historical))
        std = float(np.std(historical))

        if std == 0:
            logger.info(f"{ticker}: std is zero, skipping")
            continue

        z = (current - mean) / std

        if abs(z) >= ANOMALY_THRESHOLD:
            session.add(AnomalyAlert(
                ticker=ticker,
                current_score=round(current, 4),
                baseline_mean=round(mean, 4),
                baseline_std=round(std, 4),
                z_score=round(z, 4),
                detected_at=datetime.now(timezone.utc),
            ))
            logger.info(f"{ticker}: ANOMALY DETECTED score={current} z={z:.4f}")
            alerts.append(ticker)
        else:
            logger.info(f"{ticker}: normal score={current} z={z:.4f}")

    session.commit()

    if alerts:
        logger.info(f"anomalies flagged: {alerts}")
    else:
        logger.info("no anomalies detected this run")

    return alerts
