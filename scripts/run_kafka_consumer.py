import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kafka_pipeline.consumer import consume_and_persist
from logger import get_logger

logger = get_logger("kafka.run_consumer")


def run():
    logger.info("starting kafka consumer run")
    counts = consume_and_persist(timeout_ms=10000)
    logger.info(f"done - quotes: {counts['quotes']}, articles: {counts['articles']}")


if __name__ == "__main__":
    run()
