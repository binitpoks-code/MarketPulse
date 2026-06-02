from sqlalchemy import Column, Integer, BigInteger, String, Float, Text, DateTime, Date, UniqueConstraint
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


class AnomalyAlert(Base):
    __tablename__ = "anomaly_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False)
    current_score = Column(Float)
    baseline_mean = Column(Float)
    baseline_std = Column(Float)
    z_score = Column(Float)
    detected_at = Column(DateTime(timezone=True))


class PriceHistory(Base):
    __tablename__ = "price_history"
    __table_args__ = (UniqueConstraint("ticker", "date"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False)
    date = Column(Date, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(BigInteger)


class ForecastResult(Base):
    __tablename__ = "forecast_results"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(10), nullable=False)
    forecast_date = Column(Date, nullable=False)
    predicted_close = Column(Float)
    lower_bound = Column(Float)
    upper_bound = Column(Float)
    mae = Column(Float)
    generated_at = Column(DateTime(timezone=True))
