from src.lib.models import Video
from sqlalchemy.orm import Session

def batch_add(session: Session, videos, keyword: str) -> (int, int):
    added = updated = 0
    for video in videos:
        old: Video = session.query(Video).filter(Video.url == video.url).first()
        if old:
            old_keywords = set(old.keywords)
            if keyword not in old_keywords:
                old_keywords.add(keyword)
                old.keywords = list(old_keywords)
                updated += 1
        else:
            session.add(video)
            added += 1

    session.commit()
    return added, updated

