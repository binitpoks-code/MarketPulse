import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.stocktwits import fetch_all as fetch_stocktwits
from ingestion.yahoo import fetch_all as fetch_yahoo
from ingestion.news import fetch_all as fetch_news
from logger import get_logger

logger = get_logger("ingestion")

os.makedirs("data/raw", exist_ok=True)


def run():
    logger.info("starting ingestion")

    stocktwits = fetch_stocktwits()
    with open("data/raw/stocktwits.json", "w") as f:
        json.dump(stocktwits, f, indent=2)
    logger.info(f"stocktwits: {len(stocktwits)} posts saved")

    yahoo = fetch_yahoo()
    with open("data/raw/yahoo.json", "w") as f:
        json.dump(yahoo, f, indent=2)
    logger.info(f"yahoo: {len(yahoo)} tickers saved")

    news = fetch_news()
    with open("data/raw/news.json", "w") as f:
        json.dump(news, f, indent=2)
    logger.info(f"news: {len(news)} articles saved")

    logger.info("ingestion complete")


if __name__ == "__main__":
    run()
