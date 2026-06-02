import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.finnhub import fetch_all as fetch_finnhub
from ingestion.news import fetch_all as fetch_news
from ingestion.yahoo import fetch_all as fetch_yahoo
from logger import get_logger

logger = get_logger("ingestion")

os.makedirs("data/raw", exist_ok=True)


def run():
    logger.info("starting ingestion")

    finnhub = fetch_finnhub()

    with open("data/raw/finnhub_quotes.json", "w") as f:
        json.dump(finnhub["quotes"], f, indent=2)
    logger.info(f"finnhub quotes: {len(finnhub['quotes'])} tickers saved")

    with open("data/raw/finnhub_news.json", "w") as f:
        json.dump(finnhub["news"], f, indent=2)
    logger.info(f"finnhub news: {len(finnhub['news'])} articles saved")

    news = fetch_news()
    with open("data/raw/news.json", "w") as f:
        json.dump(news, f, indent=2)
    logger.info(f"news api: {len(news)} articles saved")

    yahoo = fetch_yahoo()
    with open("data/raw/yahoo.json", "w") as f:
        json.dump(yahoo, f, indent=2)
    logger.info(f"yahoo finance: {len(yahoo)} tickers saved")

    logger.info("ingestion complete")


if __name__ == "__main__":
    run()
