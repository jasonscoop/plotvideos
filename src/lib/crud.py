from sqlalchemy.orm import Session

from src.lib.models import Video, Keyword


def get_all_keywords(session: Session) -> list[Keyword]:
    return session.query(Keyword).filter(Keyword.enabled == True).all()


def batch_add(session: Session, videos, keyword: Keyword) -> (int, int):
    added = updated = 0

    for video in videos:
        old: Video = session.query(Video).filter(Video.url == video.url).first()
        if not old:
            video.keyword_id = keyword.id
            session.add(video)
            added += 1

    session.commit()
    return added, updated
