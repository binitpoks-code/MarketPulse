import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
import psycopg2.extras
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from database.models import Base

LOCAL = dict(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")),
    dbname=os.getenv("DB_NAME", "marketpulse"),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", ""),
)

REMOTE = dict(
    host="aws-1-us-east-1.pooler.supabase.com",
    port=5432,
    dbname="postgres",
    user="postgres.fhffqhdskbspjzcxgjkc",
    password=os.getenv("SUPABASE_PASSWORD", ""),
)

TABLES = [
    "quotes",
    "articles",
    "sentiment_scores",
    "anomaly_alerts",
    "price_history",
    "forecast_results",
]


def migrate():
    remote_url = URL.create(
        drivername="postgresql+psycopg2",
        username=REMOTE["user"],
        password=REMOTE["password"],
        host=REMOTE["host"],
        port=REMOTE["port"],
        database=REMOTE["dbname"],
    )
    engine = create_engine(remote_url)
    Base.metadata.create_all(engine)
    print("schema created in Supabase")
    engine.dispose()

    local = psycopg2.connect(**LOCAL)
    remote = psycopg2.connect(**REMOTE)
    local_cur = local.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    remote_cur = remote.cursor()

    for table in TABLES:
        print(f"migrating {table}...")

        local_cur.execute(f"SELECT * FROM {table}")
        rows = local_cur.fetchall()

        if not rows:
            print(f"  {table}: 0 rows, skipping")
            continue

        cols = list(rows[0].keys())
        col_str = ", ".join(cols)
        placeholders = ", ".join(["%s"] * len(cols))

        remote_cur.execute(f"DELETE FROM {table}")

        values = [tuple(r[c] for c in cols) for r in rows]
        psycopg2.extras.execute_batch(
            remote_cur,
            f"INSERT INTO {table} ({col_str}) VALUES ({placeholders})",
            values,
            page_size=500,
        )
        remote.commit()
        print(f"  {table}: {len(rows)} rows migrated")

    local_cur.close()
    remote_cur.close()
    local.close()
    remote.close()
    print("migration complete")


if __name__ == "__main__":
    migrate()
