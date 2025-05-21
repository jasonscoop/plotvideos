from sqlalchemy import Column, Integer, String, JSON, Enum as SAEnum
from sqlalchemy.orm import declarative_base

from src.lib.connection import engine
from src.lib.consts import VideoStatus

Base = declarative_base()


class Video(Base):
    __tablename__ = 'videos2'
    id = Column(Integer, primary_key=True, autoincrement=True)
    host = Column(String(50), nullable=False)
    original_id = Column(String(80), nullable=False)
    title = Column(String(512), nullable=False)
    url = Column(String(512), nullable=False, unique=True)
    keywords = Column(JSON, nullable=False, default=[])
    path = Column(String(50), nullable=False, default="")

    status = Column(SAEnum(VideoStatus), default=VideoStatus.added, nullable=False)
    failed_reason = Column(String(1000), nullable=False, default="")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
