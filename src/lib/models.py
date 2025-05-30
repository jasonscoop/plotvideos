from sqlalchemy import Column, Integer, String, Enum as SAEnum, Table, ForeignKey, Boolean, DateTime, JSON
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

from src.lib.connection import engine
from src.lib.consts import VideoStatus

Base = declarative_base()

# Association table for many-to-many relationship between videos and keywords
video_keywords = Table(
    'video_keywords',
    Base.metadata,
    Column('video_id', Integer, ForeignKey('videos.id')),
    Column('keyword_id', Integer, ForeignKey('keywords.id'))
)


class Keyword(Base):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    enabled = Column(Boolean, nullable=False, default=True)
    videos = relationship("Video", secondary=video_keywords, back_populates="keywords")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    host = Column(String(50), nullable=False)
    original_id = Column(String(80), nullable=False)
    title = Column(String(512), nullable=False)
    url = Column(String(512), nullable=False, unique=True)
    video_filename = Column(String(100), nullable=False, default="")
    bunny_response = Column(JSON, nullable=False, default={})
    title_translations = Column(JSON, nullable=False, default=[])
    status = Column(SAEnum(VideoStatus), default=VideoStatus.fetched, nullable=False)
    failed_reason = Column(String(1000), nullable=False, default="")

    downloaded_title = Column(String(512), nullable=False, default="")
    downloaded_description = Column(String(1000), nullable=False, default="")
    downloaded_duration = Column(Integer, nullable=False, default=0)
    downloaded_tags = Column(JSON, nullable=False, default=[])
    downloaded_categories = Column(JSON, nullable=False, default=[])

    keywords = relationship("Keyword", secondary=video_keywords, back_populates="videos")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
