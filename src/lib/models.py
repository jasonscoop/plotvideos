from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, JSON, Text
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

from src.lib.connection import engine
from src.lib.enums import VideoStatus

Base = declarative_base()


class Keyword(Base):
    __tablename__ = 'keywords'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    enabled = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class Video(Base):
    __tablename__ = 'videos'
    id = Column(Integer, primary_key=True, autoincrement=True)
    host = Column(String(50), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    original_id = Column(String(80), nullable=False)
    url = Column(String(512), nullable=False, unique=True)
    filename = Column(String(100), nullable=False, default="")
    keyword = Column(String(50), nullable=False)

    status = Column(Enum(VideoStatus), default=VideoStatus.fetched, nullable=False)
    failed_reason = Column(String(1000), nullable=False, default="")

    tags = Column(JSON, nullable=False, default=[])
    categories = Column(JSON, nullable=False, default=[])
    file_size = Column(Integer, nullable=False, default=0)
    duration = Column(Integer, nullable=False, default=0)

    title_translations = Column(JSON, nullable=False, default={})
    tag_translations = Column(JSON, nullable=False, default={})
    category_translations = Column(JSON, nullable=False, default={})

    subtitle_content = Column(Text, nullable=False, default="")
    bunny_video_id = Column(String(48), nullable=False, default="")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
