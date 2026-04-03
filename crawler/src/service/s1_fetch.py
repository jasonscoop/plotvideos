import traceback
import zlib
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from loguru import logger

from crud.keyword_crud import KeywordCrud
from crud.video_crud import VideoCrud
from core.config import (
    RAPIDAPI_KEY,
    RAPIDAPI_URL,
    S1_FETCH_MAX_PAGES,
    S1_KEYWORD_COOLDOWN_HOURS,
)
from core.enums import VideoStatus
from core.models import Video, Keyword


def _log_page_summary(keyword_name: str, page_1based: int, by_host: Dict[str, Tuple[int, int, int]]) -> None:
    lines = [
        f"{host}: {added + updated} / {fetched}"
        for host, (added, updated, fetched) in sorted(by_host.items())
    ]
    body = "; ".join(lines) if lines else "(no links)"
    logger.info(f"[{keyword_name}-{page_1based}] added/fetched: {body}")


def fetch_video_urls(query: str, page: int):
    querystring = {"query": query, "page": str(page), "timeout": "5000"}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": urlparse(RAPIDAPI_URL).netloc,
    }
    response = requests.get(RAPIDAPI_URL, headers=headers, params=querystring)
    response.raise_for_status()
    return response.json()


def process_batch(last_id: Optional[int]) -> Tuple[bool, Optional[int]]:
    """Fetch one batch of keywords and save their videos. Returns (had_work, next_last_id)."""
    keywords: List[Keyword] = KeywordCrud.batch_get(
        last_id=last_id, cooldown_hours=S1_KEYWORD_COOLDOWN_HOURS
    )
    if not keywords:
        return False, None

    exception_count = 0
    for page in range(0, S1_FETCH_MAX_PAGES):
        for keyword in keywords:
            by_host: Dict[str, Tuple[int, int, int]] = defaultdict(lambda: (0, 0, 0))

            data = fetch_video_urls(keyword.name, page + 1)
            sites = data.get("data", [])
            for site in sites:
                if not site["links"]:
                    continue

                videos = []
                site_host = site["site"]["host"]

                try:
                    for link in site["links"]:
                        title = link.get("title")
                        if not title:
                            continue

                        url = link.get("url")
                        if not url:
                            continue

                        new_video = Video(
                            title=link.get("title"),
                            url=url,
                            url_crc32=zlib.crc32(url.encode()),
                            thumbnail_url=link.get("image"),
                            host=site_host,
                            status=VideoStatus.fetched,
                            keyword_id=keyword.id,
                        )
                        videos.append(new_video)
                    if videos:
                        added, updated = VideoCrud.batch_add_or_update(videos)
                        a, u, f = by_host[site_host]
                        by_host[site_host] = (a + added, u + updated, f + len(videos))
                except Exception:
                    exception_count += 1
                    if exception_count >= 3:
                        raise
                    traceback.print_exc()

            _log_page_summary(keyword.name, page + 1, dict(by_host))

    for keyword in keywords:
        KeywordCrud.touch_fetched(keyword.id)

    return True, keywords[-1].id


def fetch_and_save_videos():
    last_id = None
    while True:
        had_work, last_id = process_batch(last_id)
        if not had_work:
            break
