from typing import List

from src.lib.models import Video, Keyword


class KeywordCrud:
    @classmethod
    def batch_get(cls, last_id: int, batch_size: int = 10) -> List[Keyword]:
        with get_db() as session:
            return session.query(Keyword) \
                .filter(Keyword.enabled == True, Keyword.id > last_id) \
                .order_by(Keyword.id.asc()) \
                .limit(batch_size) \
                .all()

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
