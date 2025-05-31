from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, JSON, Text, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

from src.lib.connection import engine
from src.lib.consts import VideoStatus

Base = declarative_base()


class Keyword(Base):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    enabled = Column(Boolean, nullable=False, default=True)

    # Relationship
    videos = relationship("Video", back_populates="keyword")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class VideoTerms(Base):
    __tablename__ = 'video_terms'
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey('videos.id'), nullable=False)
    term_id = Column(Integer, ForeignKey('terms.id'), nullable=False)
    type = Column(String(20), nullable=False)  # 'category' or 'tag'

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    host = Column(String(50), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    original_id = Column(String(80), nullable=False)
    url = Column(String(512), nullable=False, unique=True)
    video_filename = Column(String(100), nullable=False, default="")
    keyword_id = Column(Integer, ForeignKey('keywords.id'), nullable=True)
    title_translations = Column(JSON, nullable=False, default={})
    status = Column(Enum(VideoStatus), default=VideoStatus.fetched, nullable=False)
    failed_reason = Column(String(1000), nullable=False, default="")

    downloaded_title = Column(String(512), nullable=False, default="")
    downloaded_description = Column(String(1000), nullable=False, default="")
    downloaded_duration = Column(Integer, nullable=False, default=0)
    downloaded_tags = Column(JSON, nullable=False, default=[])
    downloaded_categories = Column(JSON, nullable=False, default=[])

    pre_detected_result = Column(JSON, nullable=False, default={})

    file_size = Column(Integer, nullable=False, default=0)
    subtitle_content = Column(Text, nullable=False, default="")
    duration = Column(Integer, nullable=False, default=0)
    bunny_video_id = Column(String(48), nullable=False, default="")

    # Relationships
    keyword = relationship("Keyword", back_populates="videos")
    terms = relationship("Terms", secondary="video_terms", backref="videos")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Terms(Base):
    __tablename__ = 'terms'
    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String(200), nullable=False)
    lang = Column(String(2), nullable=False, default="")
    translation = Column(String(200), nullable=False, default="")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
