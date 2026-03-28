from datetime import datetime, timedelta, timezone
from typing import List

from core.connection import get_db
from core.models import Keyword, Video


class KeywordCrud:
    @classmethod
    def batch_get(
        cls,
        last_id: int | None,
        batch_size: int = 10,
        *,
        cooldown_hours: int = 24,
    ) -> List[Keyword]:
        with get_db() as session:
            query = session.query(Keyword).filter(Keyword.enabled == True)
            if cooldown_hours > 0:
                cutoff = datetime.now(timezone.utc) - timedelta(hours=cooldown_hours)
                query = query.filter(Keyword.updated_at < cutoff)
            if last_id is not None:
                query = query.filter(Keyword.id > last_id)
            return query.order_by(Keyword.updated_at.asc(), Keyword.id.asc()).limit(
                batch_size
            ).all()

    @classmethod
    def touch_fetched(cls, keyword_id: int) -> None:
        """Mark keyword as just fetched (bumps `updated_at`) for cooldown."""
        with get_db() as session:
            session.query(Keyword).filter(Keyword.id == keyword_id).update(
                {"updated_at": datetime.now(timezone.utc)}
            )
            session.commit()

    @classmethod
    def batch_add(cls, videos, keyword: Keyword) -> (int, int):
        added = updated = 0
        with get_db() as session:
            for video in videos:
                old: Video = session.query(Video).filter(Video.url == video.url).first()
                if not old:
                    video.keyword_id = keyword.id
                    session.add(video)
                    added += 1

            session.commit()
        return added, updated
