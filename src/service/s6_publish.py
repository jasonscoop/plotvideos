from base64 import b64encode
from typing import Dict, Tuple

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from src.lib.config import WP_BASE_URL, WP_USERNAME, WP_PASSWORD
from src.lib.connection import engine
from src.lib.consts import VideoStatus, VIDEO_EMBED_TEMPLATE, BigLanguage
from src.lib.models import Video

# === Configuration ===
API_URL = f"{WP_BASE_URL}/wp-json/wp/v2/posts"
CREDENTIALS = b64encode(f"{WP_USERNAME}:{WP_PASSWORD}".encode()).decode("utf-8")
HEADERS = {
    "Authorization": f"Basic {CREDENTIALS}",
    "Content-Type": "application/json"
}


def create_post(client: httpx.Client, title: str, content: str, lang: str, image_url: str) -> Dict:
    """Create a new WordPress post."""
    data = {
        "title": title,
        "content": content,
        "status": "publish",
        "lang": lang,
        "meta": {
            "_harikrutfiwu_url": image_url,
            "_harikrutfiwu_alt": title
        }
    }

    response = client.post(API_URL, json=data, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def link_posts(client: httpx.Client, link_maps: dict) -> Dict:
    """Link English and Chinese posts together."""
    link_data = {
        "posts": link_maps
    }

    response = client.post(
        f"{WP_BASE_URL}/wp-json/custom/v1/link-posts",
        json=link_data,
        headers=HEADERS
    )
    return response.json()


def publish_video_to_wordpress(video: Video) -> Tuple[bool, str]:
    content = VIDEO_EMBED_TEMPLATE.format(library_id=0, video_id=0)
    try:
        with httpx.Client() as client:
            lang_post_maps = {}
            for lang in BigLanguage:
                # Create English post
                post = create_post(
                    client=client,
                    title=f"Video {video.id}",  # todo: You might want to use a better title
                    content=content,  # todo: You might want to use better content
                    lang=lang.short_code,
                    image_url=video.url  # You might want to use a thumbnail URL instead
                )
                lang_post_maps[lang.short_code] = post["id"]
                logger.info(f"✅ [{lang}] post created with ID: {post['id']}")

            # Link the posts
            link_result = link_posts(client, lang_post_maps)
            logger.info("✅ Posts linked:", link_result)

            return True, ""
    except Exception as e:
        return False, str(e)


def process_pending_videos():
    with Session(engine) as session:
        pending_videos = session.query(Video).filter(
            Video.status == VideoStatus.subtitle_translated
        ).all()

        for video in pending_videos:
            success, error = publish_video_to_wordpress(video)
            if success:
                video.status = VideoStatus.published
                logger.info(f"Successfully published video {video.id}")
            else:
                video.status = VideoStatus.publish_failed
                video.failed_reason = error[:1000]
                logger.info(f"Failed to publish video {video.id}: {error}")

            session.commit()


if __name__ == "__main__":
    process_pending_videos()
