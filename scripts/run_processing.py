import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from processing.cleaner import process_quotes, process_articles, process_prices
from logger import get_logger

logger = get_logger("processing")

os.makedirs("data/processed", exist_ok=True)


def run():
    logger.info("starting processing")

    quotes = process_quotes()
    if not quotes.empty:
        quotes.to_csv("data/processed/quotes.csv", index=False)
        logger.info(f"saved quotes.csv ({len(quotes)} rows)")

    articles = process_articles()
    if not articles.empty:
        articles.to_csv("data/processed/articles.csv", index=False)
        logger.info(f"saved articles.csv ({len(articles)} rows)")

    prices = process_prices()
    if not prices.empty:
        prices.to_csv("data/processed/prices.csv", index=False)
        logger.info(f"saved prices.csv ({len(prices)} rows)")

    logger.info("processing complete")


if __name__ == "__main__":
    run()
