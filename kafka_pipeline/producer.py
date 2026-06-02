import json
from kafka import KafkaProducer as _KafkaProducer
from config import KAFKA_BOOTSTRAP_SERVERS
from logger import get_logger

logger = get_logger("kafka.producer")

TOPIC_QUOTES = "market-quotes"
TOPIC_NEWS = "market-news"


class MarketPulseProducer:
    def __init__(self):
        self._producer = _KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v, default=str).encode("utf-8"),
            key_serializer=lambda k: k.encode("utf-8") if k else None,
            acks="all",
            retries=3,
        )

    def publish_quote(self, quote):
        ticker = quote.get("ticker", "UNKNOWN")
        self._producer.send(TOPIC_QUOTES, key=ticker, value=quote)

    def publish_article(self, article):
        ticker = article.get("ticker") or "MARKET"
        self._producer.send(TOPIC_NEWS, key=ticker, value=article)

    def flush(self):
        self._producer.flush()
        logger.info("all messages flushed to broker")

    def close(self):
        self._producer.close()
