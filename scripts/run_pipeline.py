import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.run_ingestion import run as ingest
from scripts.run_processing import run as process
from scripts.run_sentiment import run as sentiment
from scripts.run_anomaly import run as anomaly
from scripts.run_forecast import run as forecast
from logger import get_logger

logger = get_logger("pipeline")


def run():
    logger.info("=== pipeline start ===")

    logger.info("step 1/5: ingestion")
    ingest()

    logger.info("step 2/5: processing")
    process()

    logger.info("step 3/5: sentiment")
    sentiment()

    logger.info("step 4/5: anomaly detection")
    anomaly()

    logger.info("step 5/5: forecasting")
    try:
        forecast()
    except Exception as e:
        logger.warning(f"forecasting skipped: {e}")

    logger.info("=== pipeline complete ===")


if __name__ == "__main__":
    run()
