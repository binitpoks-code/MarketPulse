import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.finnhub import fetch_all as fetch_finnhub
from ingestion.news import fetch_all as fetch_news
from kafka_pipeline.producer import MarketPulseProducer
from logger import get_logger

logger = get_logger("kafka.run_producer")


def run():
    logger.info("starting kafka producer run")
    producer = MarketPulseProducer()

    try:
        finnhub = fetch_finnhub()

        for quote in finnhub["quotes"]:
            producer.publish_quote(quote)
        logger.info(f"published {len(finnhub['quotes'])} quotes to market-quotes")

        for article in finnhub["news"]:
            producer.publish_article(article)
        logger.info(f"published {len(finnhub['news'])} finnhub articles to market-news")

        news = fetch_news()
        for article in news:
            producer.publish_article(article)
        logger.info(f"published {len(news)} news api articles to market-news")

        producer.flush()

    finally:
        producer.close()

    logger.info("kafka producer run complete")


if __name__ == "__main__":
    run()
