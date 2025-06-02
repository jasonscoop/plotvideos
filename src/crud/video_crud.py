from typing import List

from sqlalchemy.orm import undefer

from src.lib.connection import get_db
from src.lib.consts import VideoStatus
from src.lib.models import Video


class VideoCrud:
    @classmethod
    def batch_get(cls, last_id: int, batch_size: int, status: VideoStatus) -> List[Video]:
        with get_db() as session:
            return session.query(Video) \
                .options(undefer("*")) \
                .filter(Video.status == status, Video.id > last_id) \
                .order_by(Video.id.asc()) \
                .limit(batch_size) \
                .all()

    @classmethod
    def update_meta_translations(cls,
                                 video_id: int,
                                 title_translations: dict,
                                 tag_translations: dict,
                                 category_translations: dict) -> None:
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()
            if video:
                video.title_translations = title_translations
                video.tag_translations = tag_translations
                video.category_translations = category_translations
                video.status = VideoStatus.meta_translated
                session.commit()

    @classmethod
    def update_status(cls, video_id: int, status: VideoStatus, reason: str = ""):
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = status
                video.reason = reason
                session.commit()
