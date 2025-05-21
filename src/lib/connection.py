from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from celery import Celery
from src.lib.config import POSTGRES_URL, REDIS_HOST, REDIS_PORT

engine = create_engine(POSTGRES_URL, pool_pre_ping=True, pool_size=10,)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

