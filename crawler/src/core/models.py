from typing import TYPE_CHECKING

from loguru import logger
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Boolean,
    DateTime,
    JSON,
    Text,
    Float,
    UniqueConstraint,
    Index,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, declared_attr, relationship
from sqlalchemy.sql import func

from core.connection import engine
from core.enums import VideoStatus, ThumbnailStatus

if TYPE_CHECKING:
    from core.schemas import StorePath

Base = declarative_base()


class BaseModel:
    @declared_attr
    def created_at(cls):
        return Column(
            DateTime(timezone=True), server_default=func.now(), nullable=False
        )
    
    @declared_attr
    def updated_at(cls):
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )


class Keyword(Base, BaseModel):
    __tablename__ = "keywords"
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    enabled = Column(Boolean, nullable=False, default=True)


class Video(Base, BaseModel):
    __tablename__ = "videos"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    host = Column(String(50), nullable=False, index=True)
    title = Column(String(2000), nullable=False)
    url = Column(String(2000), nullable=False, unique=True)
    url_crc32 = Column(BigInteger, nullable=False, default=0, index=True)
    thumbnail_url = Column(String(2000), nullable=False, default="")
    thumbnail_status = Column(
        Integer, nullable=False, default=ThumbnailStatus.pending.value
    )
    store_dir = Column(String(100), nullable=False, default="")
    filename = Column(String(100), nullable=False, default="")
    keyword_id = Column(Integer, ForeignKey("keywords.id"), nullable=False, index=True)
    keyword = relationship("Keyword", lazy="selectin")

    status = Column(String(20), default=VideoStatus.fetched.value, nullable=False)
    failed_reason = Column(String(1000), nullable=False, default="")

    tags = Column(JSON, nullable=False, default=[])
    categories = Column(JSON, nullable=False, default=[])
    file_size = Column(Integer, nullable=False, default=0)
    width = Column(Integer, nullable=False, default=0)
    height = Column(Integer, nullable=False, default=0)
    aspect_ratio = Column(Float, nullable=False, default=0.0)
    duration = Column(Integer, nullable=False, default=0)

    word_count = Column(Integer, nullable=False, default=0)
    word_density = Column(Float, nullable=False, default=0.0)
    failed_count = Column(Integer, nullable=False, default=0)

    __table_args__ = (Index("idx_id_status", "id", "status"),)

    @property
    def store_path(self) -> "StorePath":
        from core.schemas import StorePath

        if not self.id:
            logger.error("Video id is not set")
        return StorePath(self.id)

    @property
    def subtitle_content(self) -> str:
        vtt_path = self.store_path.vtt
        if vtt_path.exists():
            return vtt_path.read_text()
        return ""


class TitleTranslation(Base, BaseModel):
    __tablename__ = "title_translations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
    lang = Column(String(2), nullable=False)
    translated_title = Column(String(512), nullable=False)
    
    __table_args__ = (UniqueConstraint("video_id", "lang", name="uix_video_id_lang"),)


class Term(Base, BaseModel):
    __tablename__ = "terms"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    text = Column(String(255), nullable=False)
    lang = Column(String(2), nullable=False)
    translation = Column(Text, nullable=False)

    __table_args__ = (UniqueConstraint("text", "lang", name="uix_text_lang"),)


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
