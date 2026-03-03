from uuid import UUID

from loguru import logger
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    String,
    Enum,
    Boolean,
    DateTime,
    JSON,
    Text,
    Float,
    UniqueConstraint,
    Index,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import declarative_base, declared_attr, relationship
from sqlalchemy.sql import func
from uuid_utils import uuid7

from crawler.lib.connection import engine
from crawler.lib.enums import VideoStatus, ThumbnailStatus
from crawler.lib.schemas import StorePath

Base = declarative_base()


def generate_uuid7() -> UUID:
    return UUID(bytes=uuid7().bytes)


class BaseModel:
    id = Column(PgUUID(as_uuid=True), primary_key=True, default=generate_uuid7)
    
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
    thumbnail_status = Column(
        Integer, nullable=False, default=ThumbnailStatus.pending.value
    )
    store_dir = Column(String(100), nullable=False, default="")
    filename = Column(String(100), nullable=False, default="")
    keyword_id = Column(PgUUID(as_uuid=True), ForeignKey("keywords.id"), nullable=False, index=True)
    keyword = relationship("Keyword", lazy="selectin")

    status = Column(Enum(VideoStatus), default=VideoStatus.fetched, nullable=False)
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

    __table_args__ = (Index("idx_id_status", "id", "status"),)

    @property
    def store_path(self) -> StorePath:
        if not self.host or not self.original_id:
            logger.error(f"[{self.id}] host or original_id is not set")
        return StorePath(self.host, self.original_id)

    @property
    def subtitle_content(self) -> str:
        vtt_path = self.store_path.vtt
        if vtt_path.exists():
            return vtt_path.read_text()
        return ""


class TitleTranslation(Base, BaseModel):
    __tablename__ = "title_translations"
    video_id = Column(PgUUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False, index=True)
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
    aliases = Column(JSON, nullable=False, default=[])
    enabled = Column(Boolean, nullable=False, default=True)


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
