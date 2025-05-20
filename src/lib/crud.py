from src.lib.models import Video
from sqlalchemy.orm import Session

def batch_add(session: Session, videos):
    """
    Add multiple Video objects to the database, ignoring duplicates by url.
    Returns the count of actually added videos.
    Efficient for large tables: only queries for the URLs in the batch.
    """
    if not videos:
        return 0
    # Only check for duplicates among the batch URLs
    urls = [video.url for video in videos]
    # Query only for URLs in this batch
    existing = session.query(Video.url).filter(Video.url.in_(urls)).all()
    existing_urls = {url for (url,) in existing}
    to_add = [video for video in videos if video.url not in existing_urls and video.title]
    if to_add:
        session.add_all(to_add)
        session.commit()
    return len(to_add)
