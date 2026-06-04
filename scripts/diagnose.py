import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2
from dotenv import load_dotenv
load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=os.getenv("DB_PORT", 5432),
    user=os.getenv("DB_USER", "postgres"),
    password=os.getenv("DB_PASSWORD", ""),
    dbname=os.getenv("DB_NAME", "marketpulse"),
)
cur = conn.cursor()

tables = ["quotes", "articles", "sentiment_scores", "anomaly_alerts", "price_history", "forecast_results"]
for t in tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {t}")
        print(f"{t}: {cur.fetchone()[0]} rows")
    except Exception as e:
        conn.rollback()
        print(f"{t}: ERROR - {e}")

print()
cur.execute("SELECT ticker, COUNT(*) FROM articles GROUP BY ticker ORDER BY ticker NULLS FIRST")
print("articles by ticker:")
for row in cur.fetchall():
    print(f"  ticker={repr(row[0])}: {row[1]}")

print()
cur.execute("SELECT ticker, detected_at FROM anomaly_alerts ORDER BY detected_at DESC LIMIT 5")
print("recent anomaly alerts:")
rows = cur.fetchall()
if rows:
    for row in rows:
        print(f"  {row[0]} at {row[1]}")
else:
    print("  (none)")

print()
cur.execute("SELECT ticker, headline, sentiment_compound FROM articles WHERE ticker='AAPL' LIMIT 3")
print("sample AAPL articles:")
rows = cur.fetchall()
if rows:
    for row in rows:
        print(f"  [{row[0]}] sc={row[2]:.3f} | {row[1][:60]}")
else:
    print("  (none)")

cur.close()
conn.close()
print("\ndone")
