import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db import init_db, get_session
from pipeline.sentiment import load_quotes, load_and_score_articles, upsert_articles, aggregate_sentiment
from logger import get_logger

logger = get_logger("sentiment")


def run():
    logger.info("starting sentiment scoring")

    init_db()
    session = get_session()

    try:
        load_quotes(session)
        records = load_and_score_articles()
        upsert_articles(session, records)
        aggregate_sentiment(session)
        logger.info("sentiment scoring complete")
    except Exception as e:
        session.rollback()
        logger.error(f"sentiment scoring failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run()
