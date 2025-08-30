import time
import traceback
from typing import List
from urllib.parse import urlparse

import requests
from loguru import logger

from src.crud.keyword_crud import KeywordCrud
from src.crud.video_crud import VideoCrud
from src.lib.config import RAPIDAPI_KEY, RAPIDAPI_URL, S1_FETCH_MAX_PAGES
from src.lib.consts import WEBSITES
from src.lib.enums import VideoStatus
from src.lib.models import Video, Keyword
from src.lib.schemas import StorePath


def fetch_video_urls(query: str, page: int):
    querystring = {"query": query, "page": str(page), "timeout": "5000"}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": urlparse(RAPIDAPI_URL).netloc,
    }
    response = requests.get(RAPIDAPI_URL, headers=headers, params=querystring)
    response.raise_for_status()
    return response.json()


def fetch_and_save_videos(host: str = ""):
    last_id = 0
    exception_count = 0

    while True:
        keywords: List[Keyword] = KeywordCrud.batch_get(last_id=last_id)
        if not keywords:
            logger.info("All fetching, sleeping for 1 hour")
            time.sleep(1 * 60 * 60)
            last_id = 0
            continue

        last_id = keywords[-1].id
        for keyword in keywords:
            logger.info(f"[{keyword.name}] keyword fetching started")

            for page in range(0, S1_FETCH_MAX_PAGES):
                data = fetch_video_urls(keyword.name, page + 1)
                sites = data.get("data", [])
                for site in sites:
                    if not site["links"]:
                        continue

                    videos = []
                    host = site["site"]["host"]
                    name = site["site"]["name"]
                    id_extractor = WEBSITES.get(host)[1]()
                    if not id_extractor:
                        logger.error("❌ Can not find a extractor for host %s", host)
                        continue

                    try:
                        for link in site["links"]:
                            title = link.get("title")
                            if not title:
                                continue

                            original_id = id_extractor.get(link.get("url"))
                            if not original_id:
                                logger.error(
                                    f"❌ Can not find a id from: {link.get('url')}"
                                )
                                continue

                            new_video = Video(
                                title=link.get("title"),
                                url=link.get("url"),
                                thumbnail_url=link.get("image"),
                                original_id=original_id,
                                host=host,
                                status=VideoStatus.fetched,
                                keyword=keyword.name,
                                author_name=link.get("channel", "").get("name", ""),
                                author_url=link.get("channel", "").get("url", ""),
                                store_dir=StorePath.build_prefix(host, original_id),
                            )
                            videos.append(new_video)
                        added, updated = VideoCrud.batch_add_or_update(videos)
                        logger.info(
                            f"[{name}] fetched [{len(videos)}], added [{added}], updated [{updated}]"
                        )
                    except Exception as e:
                        exception_count += 1
                        if exception_count >= 3:
                            raise e
                        traceback.print_exc()
