from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Quote(Base):
    __tablename__ = "quotes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False)
    current_price = Column(Float)
    change = Column(Float)
    percent_change = Column(Float)
    high = Column(Float)
    low = Column(Float)
    open = Column(Float)
    prev_close = Column(Float)
    fetched_at = Column(DateTime)


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_type = Column(String(20))
    ticker = Column(String(10))
    headline = Column(Text)
    body = Column(Text)
    url = Column(String(500), unique=True)
    source_name = Column(String(100))
    published_at = Column(DateTime(timezone=True))
    fetched_at = Column(DateTime)
    sentiment_neg = Column(Float)
    sentiment_neu = Column(Float)
    sentiment_pos = Column(Float)
    sentiment_compound = Column(Float)


class SentimentScore(Base):
    __tablename__ = "sentiment_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False)
    score = Column(Float)
    article_count = Column(Integer)
    window_hours = Column(Integer)
    scored_at = Column(DateTime(timezone=True))
