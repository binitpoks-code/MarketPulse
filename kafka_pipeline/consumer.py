import json
from datetime import datetime, timezone
from kafka import KafkaConsumer as _KafkaConsumer
from database.db import get_session
from database.models import Quote, Article
from config import KAFKA_BOOTSTRAP_SERVERS
from logger import get_logger

logger = get_logger("kafka.consumer")

TOPICS = ["market-quotes", "market-news"]


def _write_quote(session, record):
    fetched_at = record.get("fetched_at")
    if isinstance(fetched_at, str):
        fetched_at = datetime.fromisoformat(fetched_at)

    session.add(Quote(
        ticker=record.get("ticker"),
        current_price=record.get("current_price"),
        change=record.get("change"),
        percent_change=record.get("percent_change"),
        high=record.get("high"),
        low=record.get("low"),
        open=record.get("open"),
        prev_close=record.get("prev_close"),
        fetched_at=fetched_at,
    ))


def _write_article(session, record):
    url = (record.get("url") or "").strip()
    if not url:
        return False

    if session.query(Article.id).filter_by(url=url).first():
        return False

    headline = (record.get("headline") or record.get("title") or "").strip()
    body = (record.get("summary") or record.get("description") or record.get("content") or "").strip()

    if not headline or not body:
        return False

    published_at = record.get("published_at")
    if isinstance(published_at, str):
        try:
            published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except ValueError:
            published_at = None

    fetched_at = record.get("fetched_at")
    if isinstance(fetched_at, str):
        fetched_at = datetime.fromisoformat(fetched_at)

    session.add(Article(
        source_type=record.get("source", "unknown"),
        ticker=record.get("ticker"),
        headline=headline,
        body=body,
        url=url,
        source_name=record.get("source_name", ""),
        published_at=published_at,
        fetched_at=fetched_at,
    ))
    return True


def consume_and_persist(timeout_ms=10000, group_id="marketpulse-processor"):
    """
    Polls both Kafka topics until no new messages arrive for timeout_ms milliseconds,
    then commits everything to PostgreSQL and exits.
    """
    consumer = _KafkaConsumer(
        *TOPICS,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        group_id=group_id,
        value_deserializer=lambda v: json.loads(v.decode("utf-8")),
        key_deserializer=lambda k: k.decode("utf-8") if k else None,
        auto_offset_reset="earliest",
        consumer_timeout_ms=timeout_ms,
        enable_auto_commit=True,
    )

    session = get_session()
    quote_count = 0
    article_count = 0

    try:
        for message in consumer:
            if message.topic == "market-quotes":
                _write_quote(session, message.value)
                quote_count += 1
            elif message.topic == "market-news":
                if _write_article(session, message.value):
                    article_count += 1

        session.commit()
        logger.info(f"persisted {quote_count} quotes and {article_count} articles to PostgreSQL")

    except Exception as e:
        session.rollback()
        logger.error(f"consumer error, rolled back: {e}")
        raise
    finally:
        session.close()
        consumer.close()

    return {"quotes": quote_count, "articles": article_count}
