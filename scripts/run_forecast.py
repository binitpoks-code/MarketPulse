import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from database.db import init_db, get_session, engine
from pipeline.forecaster import run_forecasts
from logger import get_logger

logger = get_logger("forecaster")


def reset_forecast_table():
    # drop and recreate so schema changes apply cleanly on dev
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS forecast_results"))
        conn.commit()


def run():
    logger.info("starting price forecasting")

    reset_forecast_table()
    init_db()
    session = get_session()

    try:
        run_forecasts(session)
        logger.info("forecasting complete")
    except Exception as e:
        session.rollback()
        logger.error(f"forecasting failed: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    run()
