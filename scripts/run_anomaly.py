import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, get_session
from pipeline.anomaly import detect_anomalies
from logger import get_logger

logger = get_logger("anomaly")


def run():
    logger.info("starting anomaly detection")

    init_db()
    session = get_session()

    try:
        detect_anomalies(session)
        logger.info("anomaly detection complete")
    except Exception as e:
        session.rollback()
        logger.error(f"anomaly detection failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run()
