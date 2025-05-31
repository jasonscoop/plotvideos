import traceback
from base64 import b64encode
from typing import Dict, List

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from src.lib.config import WP_BASE_URL, WP_USERNAME, WP_PASSWORD, BUNNY_LIBRARY_ID, BUNNY_CDN_DOMAIN
from src.lib.connection import engine
from src.lib.consts import VideoStatus, VIDEO_EMBED_TEMPLATE, BigLanguage, DB_ERROR_LOG_LENGTH
from src.lib.models import Video
from src.utils.log_utils import init_logging

# === Configuration ===
API_URL = f"{WP_BASE_URL}/wp-json/wp/v2"
CREDENTIALS = b64encode(f"{WP_USERNAME}:{WP_PASSWORD}".encode()).decode("utf-8")
HEADERS = {
    "Authorization": f"Basic {CREDENTIALS}",
    "Content-Type": "application/json"
}


def create_or_get_terms(terms: List[str], taxonomy: str, lang: str) -> List[int]:
    term_ids = []
    with httpx.Client() as client:
        # todo: map the language for terms
        for term in terms:
            response = client.get(f"{API_URL}/{taxonomy}", params={
                "search": term,
                "lang": lang,
                "per_page": 1
            })
            response.raise_for_status()
            data = response.json()
            if data:
                term_ids.append(data[0]["id"])
            else:
                create_response = client.post(
                    f"{API_URL}/{taxonomy}",
                    json={
                        "name": term,
                        "lang": lang
                    },
                    headers=HEADERS
                )
                create_response.raise_for_status()
                term_ids.append(create_response.json()["id"])

    return term_ids


def create_post(title: str, content: str,
                tags: list, categories: list, lang: str, image_url: str) -> Dict:
    tag_ids = create_or_get_terms(tags, "tags", lang)
    category_ids = create_or_get_terms(categories, "categories", lang)

    data = {
        "title": title,
        "content": content,
        "status": "publish",
        "lang": lang,
        "tags": tag_ids,
        "categories": category_ids,
        "meta": {
            "_harikrutfiwu_url": image_url,
            "_harikrutfiwu_alt": title
        }
    }

    with httpx.Client() as client:
        response = client.post(f"{API_URL}/posts", json=data, headers=HEADERS)
        response.raise_for_status()
        return response.json()


def link_posts(link_maps: dict) -> Dict:
    with httpx.Client() as client:
        response = client.post(
            f"{WP_BASE_URL}/wp-json/custom/v1/link-posts",
            json=link_maps,
            headers=HEADERS
        )
        response.raise_for_status()
        return response.json()


def publish_video_to_wordpress(video: Video):
    assert BUNNY_LIBRARY_ID and video.bunny_video_id, "Bunny library ID and video ID not set"

    video_embed = VIDEO_EMBED_TEMPLATE.format(
        library_id=BUNNY_LIBRARY_ID,
        video_id=video.bunny_video_id
    )

    categories = {c.lang: c.translation for c in video.terms if c.type == "category"}
    tags = {c.lang: c.translation for c in video.terms if c.type == "tags"}

    lang_post_maps = {}
    for lang in BigLanguage:
        post = create_post(
            title=video.title_translations.get(lang.short_code, video.title),
            content=video_embed,
            tags=tags.get(lang.short_code, video.downloaded_tags),
            categories=categories.get(lang.short_code, video.downloaded_categories),
            lang=lang.short_code,
            image_url=f"https://{BUNNY_CDN_DOMAIN}/{video.bunny_video_id}/thumbnail.jpg"
        )

        lang_post_maps[lang.short_code] = post["id"]
        logger.info(f"✅ [{lang.short_code}] post created with ID: {post['id']}")

    if len(lang_post_maps) > 1:
        link_result = link_posts(lang_post_maps)
        logger.info(f"✅ Posts linked: {link_result}")


def process_pending_videos(batch_size=10):
    last_id = 0
    while True:
        with Session(engine) as session:
            pending_videos = session.query(Video).filter(Video.status == VideoStatus.uploaded,
                                                         Video.id > last_id).limit(batch_size).all()
            if not pending_videos:
                break

            for video in pending_videos:
                try:
                    publish_video_to_wordpress(video)
                    video.status = VideoStatus.published
                    logger.info(f"Successfully published video {video.id}")
                except Exception as e:
                    video.status = VideoStatus.failed_published
                    video.failed_reason = str(e)[:DB_ERROR_LOG_LENGTH]
                    logger.error(f"Failed to publish video {video.id}: {str(e)}")
                    traceback.print_exc()

                session.commit()


if __name__ == "__main__":
    init_logging("publish")
    process_pending_videos()
