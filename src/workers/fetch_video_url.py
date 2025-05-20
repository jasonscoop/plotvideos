import requests
from urllib.parse import urlparse
import logging

from src.config import RAPIDAPI_KEY, RAPIDAPI_URL, KEYWORDS
from src.connection import engine, SessionLocal, celery_app
from src.models import Video, Base, VideoStatus
from src.crud import batch_add

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_video_urls(query: str, page: int):
    querystring = {
        "query": query,
        "page": str(page),
        "timeout": "5000"
    }
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": urlparse(RAPIDAPI_URL).netloc
    }
    response = requests.get(RAPIDAPI_URL, headers=headers, params=querystring)
    response.raise_for_status()
    return response.json()

def fetch_and_save_videos():
    max_page = 3
    session = SessionLocal()
    try:
        for keyword in KEYWORDS:
            logger.info(f"Fetching videos for keyword: {keyword}")
            page = 1
            while True:
                data = fetch_video_urls(keyword, page)
                sites = data.get('data', [])
                for site in sites:
                    if not site["links"]:
                        continue
                    videos = []
                    host = site["site"]["host"]
                    name = site["site"]["name"]
                    for link in site["links"]:
                        videos.append(Video(
                                title=link.get('title'),
                                url=link.get('url'),
                                host=host,
                                keyword=keyword,
                                status=VideoStatus.added
                            ))
                    added = batch_add(session, videos)
                    logging.info("Site [%s] get [%s] videos and added [%s]", name, len(site["links"]), added)
                page += 1
                if page > max_page:
                    break
    except Exception as e:
        logger.error(f"Error fetching/saving videos: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    fetch_and_save_videos()
