import traceback

import requests
from urllib.parse import urlparse
import logging

from src.lib.config import RAPIDAPI_KEY, RAPIDAPI_URL, KEYWORDS
from src.lib.connection import SessionLocal
from src.lib.consts import ID_EXTRACTOR_MAP
from src.lib.models import Video, VideoStatus
from src.lib.crud import batch_add

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

def fetch_and_save_videos(max_page=3):
    session = SessionLocal()

    for keyword in KEYWORDS:
        logger.info(f"Fetching videos for keyword: {keyword}")

        for page in range(1, max_page):
            data = fetch_video_urls(keyword, page)
            sites = data.get('data', [])
            for site in sites:
                if not site["links"]:
                    continue

                videos = []
                host = site["site"]["host"]
                name = site["site"]["name"]
                id_extractor = ID_EXTRACTOR_MAP.get(host)()
                if not id_extractor:
                    logger.error("Can not find a extractor for host %s", host)
                    continue

                try:
                    for link in site["links"]:
                        title = link.get('title')
                        if not title:
                            continue

                        videos.append(Video(
                                title=link.get('title'),
                                url=link.get('url'),
                                original_id=id_extractor.get(link.get('url')),
                                host=host,
                                keywords=[keyword],
                                status=VideoStatus.added
                            ))
                    added, updated = batch_add(session, videos, keyword)
                    logging.info("Site [%s] get [%s] videos and updated [%s] added [%s]", name, len(site["links"]), updated, added)
                except Exception as e:
                    logger.error(f"Error fetching/saving videos: {e}")
                    traceback.print_exc()
                    session.rollback()

            if page > max_page:
                logger.info("Reach the max page, break")
                break

    session.close()

if __name__ == "__main__":
    fetch_and_save_videos()
    logging.info("All done!")
