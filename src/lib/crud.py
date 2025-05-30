from sqlalchemy.orm import Session

from src.lib.models import Video, Keyword


def get_or_create_keyword(session: Session, keyword_name: str) -> Keyword:
    keyword = session.query(Keyword).filter(Keyword.name == keyword_name).first()
    if not keyword:
        keyword = Keyword(name=keyword_name)
        session.add(keyword)
        session.commit()
    return keyword


def get_all_keywords(session: Session) -> list[Keyword]:
    return session.query(Keyword).filter(Keyword.enabled == True).all()


def batch_add(session: Session, videos, keyword: str) -> (int, int):
    added = updated = 0
    keyword_obj = get_or_create_keyword(session, keyword)

    for video in videos:
        old: Video = session.query(Video).filter(Video.url == video.url).first()
        if old:
            if keyword_obj not in old.keywords:
                old.keywords.append(keyword_obj)
                updated += 1
        else:
            video.keywords = [keyword_obj]
            session.add(video)
            added += 1

    session.commit()
    return added, updated
