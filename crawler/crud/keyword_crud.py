from typing import List
from uuid import UUID

from crawler.core.connection import get_db
from crawler.core.models import Video, Keyword


class KeywordCrud:
    @classmethod
    def batch_get(cls, last_id: UUID | None, batch_size: int = 10) -> List[Keyword]:
        with get_db() as session:
            query = session.query(Keyword).filter(Keyword.enabled == True)
            if last_id is not None:
                query = query.filter(Keyword.id > last_id)
            return query.order_by(Keyword.id.asc()).limit(batch_size).all()

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
