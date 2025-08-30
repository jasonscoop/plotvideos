from typing import List

from sqlalchemy.orm import undefer
from sqlalchemy import text
from tenacity import stop_after_attempt, retry, wait_fixed

from src.lib.connection import get_db
from src.lib.enums import VideoStatus
from src.lib.models import Video


class VideoCrud:
    @classmethod
    def batch_get(
        cls,
        last_id: int,
        batch_size: int,
        status: VideoStatus | List[VideoStatus] | None = None,
        host: str = "",
        temp_status: int | None = None,
    ) -> List[Video]:
        with get_db() as session:
            query = (
                session.query(Video)
                .options(undefer("*"))
                .with_for_update(skip_locked=True)
            )

            if isinstance(status, list):
                query = query.filter(Video.status.in_(status), Video.id > last_id)
            elif isinstance(status, VideoStatus):
                query = query.filter(Video.status == status, Video.id > last_id)
            else:
                query = query.filter(Video.id > last_id)

            if host:
                query = query.filter(Video.host == host)

            if temp_status is not None:
                query = query.filter(Video.temp_status == temp_status)

            return query.order_by(Video.id.asc()).limit(batch_size).all()

    @classmethod
    def batch_add_or_update(cls, videos: List[Video]) -> tuple[int, int]:
        if len(videos) == 0:
            return 0, 0

        with get_db() as session:
            urls = [video.url for video in videos]

            existing_videos = session.query(Video).filter(Video.url.in_(urls)).all()
            existing_urls = {video.url: video for video in existing_videos}

            to_insert = []
            to_update = []

            for video in videos:
                if video.url in existing_urls:
                    existing_video = existing_urls[video.url]
                    if existing_video.thumbnail_url != video.thumbnail_url:
                        existing_video.thumbnail_url = video.thumbnail_url
                        to_update.append(existing_video)
                else:
                    to_insert.append(video)

            if to_insert:
                for video in to_insert:
                    session.add(video)

            session.commit()
            return len(to_insert), len(to_update)

    @staticmethod
    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3), reraise=True)
    def update(data: dict):
        if "id" not in data:
            raise KeyError("Video id is required")

        updates = {k: v for k, v in data.items() if k != "id" and v is not None}
        if not updates:
            return

        with get_db() as session:
            session.query(Video).filter(Video.id == data["id"]).update(updates)
            session.commit()

    @classmethod
    def update_status(cls, video_id: int, status: VideoStatus, reason: str = ""):
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()
            if video:
                video.status = status
                video.failed_reason = reason
                session.commit()

            return reason
