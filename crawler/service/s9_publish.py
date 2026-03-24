import time
import traceback
from os import getenv
from typing import List, Optional, Tuple

import requests
from loguru import logger

from crawler.crud.term_crud import TermCrud
from crawler.crud.video_crud import VideoCrud
from crawler.crud.video_title_translation_crud import TitleTranslationCrud
from crawler.core.config import S7_UPLOAD_BATCH_SIZE
from crawler.core.enums import VideoStatus
from crawler.core.languages import Language
from crawler.core.models import Video
from crawler.utils.signal_utils import setup_graceful_shutdown, should_stop

PLAYER_API_URL = getenv("PLAYER_API_URL", "http://localhost:8000/api/videos")


def _build_payload(video: Video, languages: List[Language]) -> dict:
    sp = video.store_path
    title_translations = TitleTranslationCrud.get_by_video_id_as_dict(video.id)

    keyword = video.keyword.name if video.keyword else ""
    tags = video.tags or []
    categories = video.categories or []

    all_terms = ([keyword] if keyword else []) + tags + categories
    term_map = TermCrud.get_translations_map(all_terms) if all_terms else {}

    translations = {}
    for lang in languages:
        lang_terms = term_map.get(lang.code, {})
        translations[lang.code] = {
            "title": title_translations.get(lang.code, ""),
            "keyword": lang_terms.get(keyword, keyword) if keyword else "",
            "tags": [lang_terms.get(t, t) for t in tags],
            "categories": [lang_terms.get(c, c) for c in categories],
        }

    subtitle_tracks = [
        {
            "lang": lang.code,
            "label": lang.native_name,
            "url": f"/media/{sp.translated_s3_key}{lang.code}.vtt",
        }
        for lang in languages
    ]

    return {
        "original_id": video.id,
        "title": video.title,
        "duration": video.duration,
        "width": video.width,
        "height": video.height,
        "thumbnail_url": f"/media/{sp.thumbnail_s3_key}",
        "video_url": f"/media/{sp.video_s3_key}",
        "hls_url": f"/media/{sp.hls_master_s3_key}",
        "store_dir": video.store_dir,
        "keyword": keyword,
        "tags": tags,
        "categories": categories,
        "translations": translations,
        "subtitle_tracks": subtitle_tracks,
    }


def _publish_one(video: Video, languages: List[Language]):
    payload = _build_payload(video, languages)
    resp = requests.post(PLAYER_API_URL, json=payload, timeout=30)
    resp.raise_for_status()
    player_id = resp.json().get("id")
    logger.info(
        f"[{video.id} | {video.host} | {video.original_id}] published to player as #{player_id}"
    )


def process_batch(last_id: Optional[int]) -> Tuple[bool, Optional[int]]:
    """Publish one batch of uploaded videos. Returns (had_work, next_last_id)."""
    languages = Language.get_all()
    videos = VideoCrud.batch_get(last_id, S7_UPLOAD_BATCH_SIZE, VideoStatus.uploaded)
    if not videos:
        return False, None

    exception_count = 0
    for video in videos:
        try:
            _publish_one(video, languages)
            VideoCrud.update_status(video.id, VideoStatus.published)
        except Exception as e:
            VideoCrud.record_failure(video.id, VideoStatus.published.log(e))
            exception_count += 1
            logger.error(
                f"[{video.id} | {video.original_id}] publish failed: {e}"
            )
            traceback.print_exc()
            if exception_count >= 3:
                raise e

    return True, videos[-1].id


def publish_videos():
    setup_graceful_shutdown()
    last_id = None
    while not should_stop():
        had_work, last_id = process_batch(last_id)
        if not had_work:
            logger.info("No uploaded videos to publish, sleeping 5 min")
            time.sleep(5 * 60)
            last_id = None
