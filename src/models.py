from sqlalchemy import Column, Integer, String, Text, Enum as SAEnum
from sqlalchemy.orm import declarative_base
import enum

from src.connection import engine

Base = declarative_base()

class VideoStatus(enum.Enum):
    added = "added"
    downloaded = "downloaded"
    subtitle_downloaded = "subtitle_downloaded"
    subtitle_translated = "subtitle_translated"
    published = "published"

class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(512), nullable=False)
    url = Column(String(512), nullable=False, unique=True)
    host = Column(String(50), nullable=False)
    keyword = Column(String(128), nullable=False)

    status = Column(SAEnum(VideoStatus), default=VideoStatus.added, nullable=False) 


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)