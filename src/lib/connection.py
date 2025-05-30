from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.lib.config import POSTGRES_URL

engine = create_engine(POSTGRES_URL, pool_pre_ping=True, pool_size=10, )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
