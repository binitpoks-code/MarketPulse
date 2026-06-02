from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
from config import DATABASE_URL
from logger import get_logger

logger = get_logger("database")

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)
    logger.info("database tables ready")


def get_session():
    return Session()
