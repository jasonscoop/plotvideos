from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, JSON, Text, Float, UniqueConstraint
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

from src.lib.connection import engine
from src.lib.enums import VideoStatus
from src.lib.schemas import StorePath

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
    author_name = Column(String(100), nullable=False, default="")
    author_url = Column(String(500), nullable=False, default="")
    url = Column(String(512), nullable=False, unique=True)
    filename = Column(String(100), nullable=False, default="")
    keyword = Column(String(50), nullable=False)

    status = Column(Enum(VideoStatus), default=VideoStatus.fetched, nullable=False)
    failed_reason = Column(String(1000), nullable=False, default="")

    tags = Column(JSON, nullable=False, default=[])
    categories = Column(JSON, nullable=False, default=[])
    file_size = Column(Integer, nullable=False, default=0)
    width = Column(Integer, nullable=False, default=0)
    height = Column(Integer, nullable=False, default=0)
    aspect_ratio = Column(Float, nullable=False, default=0.0)
    duration = Column(Integer, nullable=False, default=0)

    title_translations = Column(JSON, nullable=False, default={})

    subtitle_content = Column(Text, nullable=False, default="")
    subtitle_tokens = Column(Integer, nullable=False, default=0)
    subtitle_duration_ratio = Column(Float, nullable=False, default=0.0)

    bunny_library_id = Column(Integer, nullable=False, default=0)
    bunny_video_id = Column(String(48), nullable=False, default="", index=True)
    bunny_cdn_domain = Column(String(50), nullable=False, default="")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    @property
    def path(self) -> StorePath:
        return StorePath(self.host, self.original_id, self.filename)


class Term(Base):
    __tablename__ = 'terms'
    id = Column(Integer, primary_key=True, autoincrement=True)
    term = Column(String(255), nullable=False)
    lang = Column(String(2), nullable=False)
    translation = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('term', 'lang', name='uix_term_lang'),
    )


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
