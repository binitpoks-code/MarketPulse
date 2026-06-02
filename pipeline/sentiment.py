import pandas as pd
from datetime import datetime, timezone, timedelta
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from database.models import Article, SentimentScore, Quote
from config import SENTIMENT_WINDOW
from logger import get_logger

logger = get_logger("sentiment")

analyzer = SentimentIntensityAnalyzer()


def score_text(text):
    if not text or not str(text).strip():
        return {"neg": 0.0, "neu": 1.0, "pos": 0.0, "compound": 0.0}
    return analyzer.polarity_scores(str(text))


def load_and_score_articles(articles_path="data/processed/articles.csv"):
    df = pd.read_csv(articles_path)

    records = []
    for _, row in df.iterrows():
        combined = f"{row['headline']}. {row['body']}"
        scores = score_text(combined)

        published = pd.to_datetime(row["published_at"], utc=True).to_pydatetime() if pd.notna(row["published_at"]) else None
        fetched = pd.to_datetime(row["fetched_at"]).to_pydatetime() if pd.notna(row["fetched_at"]) else None

        records.append({
            "source_type": row["source_type"],
            "ticker": row["ticker"] if pd.notna(row["ticker"]) else None,
            "headline": row["headline"],
            "body": row["body"],
            "url": row["url"],
            "source_name": row["source_name"],
            "published_at": published,
            "fetched_at": fetched,
            "sentiment_neg": scores["neg"],
            "sentiment_neu": scores["neu"],
            "sentiment_pos": scores["pos"],
            "sentiment_compound": scores["compound"],
        })

    logger.info(f"scored {len(records)} articles")
    return records


def upsert_articles(session, records):
    existing_urls = {row[0] for row in session.query(Article.url).all()}

    new_count = 0
    for r in records:
        if r["url"] in existing_urls:
            continue
        session.add(Article(**r))
        new_count += 1

    session.commit()
    logger.info(f"inserted {new_count} new articles into database")


def aggregate_sentiment(session):
    cutoff = datetime.now(timezone.utc) - timedelta(hours=SENTIMENT_WINDOW)

    rows = (
        session.query(Article)
        .filter(Article.ticker.isnot(None))
        .filter(Article.published_at >= cutoff)
        .all()
    )

    if not rows:
        logger.warning("no articles found within sentiment window, check published_at timestamps")
        return

    by_ticker = {}
    for row in rows:
        by_ticker.setdefault(row.ticker, []).append(row.sentiment_compound)

    scored_at = datetime.now(timezone.utc)

    for ticker, scores in by_ticker.items():
        avg = round(sum(scores) / len(scores), 4)
        session.add(SentimentScore(
            ticker=ticker,
            score=avg,
            article_count=len(scores),
            window_hours=SENTIMENT_WINDOW,
            scored_at=scored_at,
        ))
        logger.info(f"{ticker}: sentiment={avg} from {len(scores)} articles")

    session.commit()


def load_quotes(session, quotes_path="data/processed/quotes.csv"):
    df = pd.read_csv(quotes_path)

    for _, row in df.iterrows():
        session.add(Quote(
            ticker=row["ticker"],
            current_price=row["current_price"],
            change=row["change"],
            percent_change=row["percent_change"],
            high=row["high"],
            low=row["low"],
            open=row["open"],
            prev_close=row["prev_close"],
            fetched_at=pd.to_datetime(row["fetched_at"]).to_pydatetime(),
        ))

    session.commit()
    logger.info(f"loaded {len(df)} quotes into database")
