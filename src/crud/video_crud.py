from typing import List

from sqlalchemy.orm import undefer

from src.lib.connection import get_db
from src.lib.enums import VideoStatus
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
    def batch_add(cls, videos: List[Video]):
        with get_db() as session:
            for video in videos:
                old = session.query(Video).filter(Video.url == video.url).first()
                if old is None:
                    session.add(video)
            session.commit()

    @staticmethod
    def update(data: dict):
        if "id" not in data:
            raise KeyError("Video id is required")

        with get_db() as session:
            old = session.query(Video).get(data["id"])
            for key, value in data.items():
                if value is not None and hasattr(old, key):
                    setattr(old, key, value)

            session.commit()

    @classmethod
    def update_status(cls, video_id: int, status: VideoStatus, reason: str = ""):
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = status
                video.reason = reason
                session.commit()
