from typing import List, Dict

from sqlalchemy.orm import undefer
from sqlalchemy import or_, text
from tenacity import stop_after_attempt, retry, wait_fixed

from core.config import MAX_FAILED_NUM
from core.connection import get_db
from core.enums import VideoStatus
from core.models import Video, TitleTranslation
from core.schemas import StorePath


class VideoCrud:
    @classmethod
    def batch_get(
        cls,
        last_id: int | None,
        batch_size: int,
        status: VideoStatus | List[VideoStatus] | None = None,
        host: str = "",
    ) -> List[Video]:
        with get_db() as session:
            query = (
                session.query(Video)
                .options(undefer("*"))
                .with_for_update(skip_locked=True)
            )

            if isinstance(status, list):
                query = query.filter(Video.status.in_(status))
            elif isinstance(status, VideoStatus):
                query = query.filter(Video.status == status)

            if last_id is not None:
                query = query.filter(Video.id > last_id)

            if host:
                query = query.filter(Video.host == host)

            query = query.filter(Video.failed_count < MAX_FAILED_NUM)

            return query.order_by(Video.id.asc()).limit(batch_size).all()

    @classmethod
    def batch_add_or_update(cls, videos: List[Video]) -> tuple[int, int]:
        if len(videos) == 0:
            return 0, 0

        # One fetch response can list the same URL twice; only the first row would match DB.
        # Without deduping, two INSERTs for the same URL hit videos_url_key.
        seen: set[str] = set()
        deduped: List[Video] = []
        for v in videos:
            if v.url in seen:
                continue
            seen.add(v.url)
            deduped.append(v)

        with get_db() as session:
            urls = list({v.url for v in deduped})
            crc32s = list({v.url_crc32 for v in deduped})
            # Load rows that may overlap this batch: same URL (unique) or same crc32 bucket.
            candidates = (
                session.query(Video)
                .filter(or_(Video.url.in_(urls), Video.url_crc32.in_(crc32s)))
                .all()
            )
            existing_by_url = {row.url: row for row in candidates}

            to_insert: List[Video] = []
            to_update: List[Video] = []

            for video in deduped:
                existing = existing_by_url.get(video.url)
                if existing is None:
                    to_insert.append(video)
                    continue

                # Same video iff URL and url_crc32 both match (canonical identity).
                same_video = existing.url_crc32 == video.url_crc32
                if same_video:
                    if existing.thumbnail_url != video.thumbnail_url:
                        existing.thumbnail_url = video.thumbnail_url
                        to_update.append(existing)
                else:
                    # Row exists for this URL but crc32 differs; cannot insert again (url unique).
                    # Reconcile stored row to incoming crc32 + thumbnail.
                    existing.url_crc32 = video.url_crc32
                    if existing.thumbnail_url != video.thumbnail_url:
                        existing.thumbnail_url = video.thumbnail_url
                    to_update.append(existing)

            if to_insert:
                for video in to_insert:
                    session.add(video)
                session.flush()
                for video in to_insert:
                    video.store_dir = StorePath.build_prefix(video.id)

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

    @classmethod
    def record_failure(cls, video_id: int, reason: str = "") -> str:
        exceeded = False
        with get_db() as session:
            video = session.query(Video).filter(Video.id == video_id).first()
            if video:
                video.failed_count = video.failed_count + 1
                video.failed_reason = reason
                if video.failed_count >= MAX_FAILED_NUM:
                    video.status = VideoStatus.retry_exceeded
                    exceeded = True
                session.commit()
        if exceeded:
            from utils.file_utils import rm_by_id
            rm_by_id(video_id)
        return reason

    @classmethod
    def get_title_translations(cls, video_id: int) -> Dict[str, str]:
        with get_db() as session:
            translations = (
                session.query(TitleTranslation)
                .filter(TitleTranslation.video_id == video_id)
                .all()
            )
            return {t.lang: t.translated_title for t in translations}

    @classmethod
    def get_by_id(cls, video_id: int) -> Video | None:
        with get_db() as session:
            return session.query(Video).filter(Video.id == video_id).first()
