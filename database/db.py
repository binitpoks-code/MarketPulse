from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from database.models import Base
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from logger import get_logger

logger = get_logger("database")

engine = create_engine(URL.create(
    drivername="postgresql+psycopg2",
    username=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=int(DB_PORT),
    database=DB_NAME,
))
Session = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)
    logger.info("database tables ready")


def get_session():
    return Session()
