import sys
import time
import traceback
from typing import List
from urllib.parse import urlparse

import requests
from loguru import logger

from src.crud.keyword_crud import KeywordCrud
from src.crud.video_crud import VideoCrud
from src.lib.config import RAPIDAPI_KEY, RAPIDAPI_URL
from src.lib.consts import WEBSITES
from src.lib.enums import VideoStatus
from src.lib.models import Video, Keyword
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


def fetch_and_save_videos(max_pages, batch_size):
    last_id = 0
    exception_count = 0

    while True:
        keywords: List[Keyword] = KeywordCrud.batch_get(last_id=last_id, batch_size=batch_size)
        if not keywords:
            time.sleep(2 * 60 * 60)
            continue

        last_id = keywords[-1].id
        for keyword in keywords:
            logger.info(f"[{keyword.name}] keyword fetching started")

            for page in range(0, max_pages):
                data = fetch_video_urls(keyword.name, page + 1)
                sites = data.get('data', [])
                for site in sites:
                    if not site["links"]:
                        continue

                    videos = []
                    host = site["site"]["host"]
                    name = site["site"]["name"]
                    id_extractor = WEBSITES.get(host)["id_extractor"]()
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
                                status=VideoStatus.fetched,
                                keyword=keyword.name,
                                author_name=link.get('channel', "").get("name", ""),
                                author_url=link.get('channel', "").get("url", ""),
                            ))
                        added = VideoCrud.batch_add(videos)
                        logger.info(f"[{name}] fetched, added [{added}/{len(videos)}]")
                    except Exception as e:
                        exception_count += 1
                        if exception_count >= 3:
                            raise e
                        traceback.print_exc()


if __name__ == "__main__":
    init_logging("fetch")
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    max_pages = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    fetch_and_save_videos(max_pages=max_pages, batch_size=batch_size)
    logger.info("All fetched")
