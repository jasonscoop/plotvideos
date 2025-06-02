import traceback
from typing import List
from urllib.parse import urlparse

import requests
from loguru import logger
from src.crud.crud import batch_add, get_all_keywords

from src.lib.config import RAPIDAPI_KEY, RAPIDAPI_URL
from src.lib.connection import SessionLocal
from src.lib.consts import ID_EXTRACTOR_MAP
from src.lib.models import Video, VideoStatus, Keyword
from src.utils.log_utils import init_logging


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
    keywords: List[Keyword] = get_all_keywords(session)

    if not keywords:
        logger.warning("No keywords found in database. Please add some keywords first.")
        return

    for keyword in keywords:
        logger.info(f"Fetching videos for keyword: {keyword}")

        for page in range(1, max_page):
            data = fetch_video_urls(keyword.name, page)
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
                            status=VideoStatus.fetched
                        ))
                    added, updated = batch_add(session, videos, keyword)
                    logger.info(f"[{name}] get [{len(site["links"])}] videos, updated [{updated}] added [{added}]")
                except Exception as e:
                    logger.error(f"Error fetching/saving videos: {e}")
                    traceback.print_exc()
                    session.rollback()

            if page > max_page:
                logger.info("Reach the max page, break")
                break

    session.close()


if __name__ == "__main__":
    init_logging("fetch")
    fetch_and_save_videos(2)
    logger.info("All done!")
