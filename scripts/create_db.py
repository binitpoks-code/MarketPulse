import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from logger import get_logger

logger = get_logger("setup")


def create_database():
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", 5432),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", ""),
        dbname="postgres",
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()

    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'marketpulse'")
    if cur.fetchone():
        logger.info("database marketpulse already exists")
    else:
        cur.execute("CREATE DATABASE marketpulse")
        logger.info("database marketpulse created")

    cur.close()
    conn.close()


if __name__ == "__main__":
    create_database()
