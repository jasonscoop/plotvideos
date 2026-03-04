from __future__ import annotations

from typing import List

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import declarative_base, declared_attr, relationship
from sqlalchemy.sql import func

from web.core.enums import VideoStatus


Base = declarative_base()


class BaseModel:
    id = Column(PgUUID(as_uuid=True), primary_key=True)

    @declared_attr
    def created_at(cls):  # type: ignore[no-untyped-def]
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            nullable=False,
        )

    @declared_attr
    def updated_at(cls):  # type: ignore[no-untyped-def]
        return Column(
            DateTime(timezone=True),
            server_default=func.now(),
            onupdate=func.now(),
            nullable=False,
        )


class Keyword(Base, BaseModel):
    __tablename__ = "keywords"

    name = Column(String(100), nullable=False, unique=True)
    enabled = Column(Boolean, nullable=False, default=True)


class Video(Base, BaseModel):
    __tablename__ = "videos"

    host = Column(String(50), nullable=False, index=True)
    title = Column(String(512), nullable=False)
    original_id = Column(String(80), nullable=False)
    author_name = Column(String(100), nullable=False, default="")
    author_url = Column(String(500), nullable=False, default="")
    url = Column(String(512), nullable=False, unique=True)
    url_crc32 = Column(BigInteger, nullable=False, default=0, index=True)
    thumbnail_url = Column(String(512), nullable=False, default="")
    thumbnail_status = Column(Integer, nullable=False, default=0)
    store_dir = Column(String(100), nullable=False, default="")
    filename = Column(String(100), nullable=False, default="")
    keyword_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("keywords.id"),
        nullable=False,
        index=True,
    )
    keyword = relationship("Keyword", lazy="selectin")

    status = Column(Enum(VideoStatus), default=VideoStatus.fetched, nullable=False)
    failed_count = Column(Integer, nullable=False, default=0)
    failed_reason = Column(String(1000), nullable=False, default="")

    tags = Column(JSON, nullable=False, default=list)
    categories = Column(JSON, nullable=False, default=list)
    file_size = Column(Integer, nullable=False, default=0)
    width = Column(Integer, nullable=False, default=0)
    height = Column(Integer, nullable=False, default=0)
    aspect_ratio = Column(Float, nullable=False, default=0.0)
    duration = Column(Integer, nullable=False, default=0)

    word_count = Column(Integer, nullable=False, default=0)
    word_density = Column(Float, nullable=False, default=0.0)

    __table_args__ = (Index("idx_id_status", "id", "status"),)

    @property
    def video_s3_key(self) -> str:
        return f"{self.store_dir}/video.mp4"

    @property
    def thumbnail_s3_key(self) -> str:
        return f"{self.store_dir}/thumbnail.webp"

    @property
    def translated_s3_key(self) -> str:
        return f"{self.store_dir}/subtitles/"

    @property
    def hls_master_s3_key(self) -> str:
        return f"{self.store_dir}/hls/master.m3u8"


class TitleTranslation(Base, BaseModel):
    __tablename__ = "title_translations"

    video_id = Column(
        PgUUID(as_uuid=True),
        ForeignKey("videos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    lang = Column(String(2), nullable=False)
    translated_title = Column(String(512), nullable=False)

    __table_args__ = (UniqueConstraint("video_id", "lang", name="uix_video_id_lang"),)


class Term(Base, BaseModel):
    __tablename__ = "terms"

    text = Column(String(255), nullable=False)
    lang = Column(String(2), nullable=False)
    translation = Column(Text, nullable=False)

    __table_args__ = (UniqueConstraint("text", "lang", name="uix_text_lang"),)


class Language(Base, BaseModel):
    __tablename__ = "languages"

    code = Column(String(2), nullable=False, unique=True)
    locale = Column(String(5), nullable=False)
    native_name = Column(String(50), nullable=False)
    aliases = Column(JSON, nullable=False, default=list)
    enabled = Column(Boolean, nullable=False, default=True)

