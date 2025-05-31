import traceback
from base64 import b64encode
from typing import Dict, Tuple, List

import httpx
from loguru import logger
from sqlalchemy.orm import Session

from src.lib.config import WP_BASE_URL, WP_USERNAME, WP_PASSWORD, BUNNY_LIBRARY_ID, BUNNY_CDN_DOMAIN
from src.lib.connection import engine
from src.lib.consts import VideoStatus, VIDEO_EMBED_TEMPLATE, BigLanguage
from src.lib.models import Video
from src.utils.log_utils import init_logging

# === Configuration ===
API_URL = f"{WP_BASE_URL}/wp-json/wp/v2"
CREDENTIALS = b64encode(f"{WP_USERNAME}:{WP_PASSWORD}".encode()).decode("utf-8")
HEADERS = {
    "Authorization": f"Basic {CREDENTIALS}",
    "Content-Type": "application/json"
}


def create_or_get_terms(client: httpx.Client, terms: List[str], taxonomy: str, lang: str) -> List[int]:
    """Create or get WordPress terms (tags or categories) and return their IDs."""
    term_ids = []

    for term in terms:
        # First try to get existing term
        response = client.get(f"{API_URL}/{taxonomy}", params={
            "search": term,
            "lang": lang,
            "per_page": 1
        })
        response.raise_for_status()

        if response.json():
            # Term exists, use its ID
            term_ids.append(response.json()[0]["id"])
        else:
            # Term doesn't exist, create it
            try:
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
            except Exception as e:
                logger.error(f"Failed to create {taxonomy} '{term}': {str(e)}")
                traceback.print_exc()
                continue

    return term_ids


def create_post(client: httpx.Client, title: str, content: str, description: str,
                tags: list, categories: list, lang: str, image_url: str) -> Dict:
    """Create a new WordPress post with translated content and term IDs."""
    # Get or create tags and categories
    tag_ids = create_or_get_terms(client, tags, "tags", lang)
    category_ids = create_or_get_terms(client, categories, "categories", lang)

    # Format the content with description and video embed
    formatted_content = f"""
{content}

{description}
"""

    data = {
        "title": title,
        "content": formatted_content,
        "status": "publish",
        "lang": lang,
        "tags": tag_ids,
        "categories": category_ids,
        "meta": {
            "_harikrutfiwu_url": image_url,
            "_harikrutfiwu_alt": title
        }
    }

    response = client.post(f"{API_URL}/posts", json=data, headers=HEADERS)
    response.raise_for_status()
    return response.json()


def link_posts(client: httpx.Client, link_maps: dict) -> Dict:
    """Link posts in different languages together."""
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
    assert BUNNY_LIBRARY_ID and video.bunny_video_id, "Bunny library ID and video ID not set"

    video_embed = VIDEO_EMBED_TEMPLATE.format(
        library_id=BUNNY_LIBRARY_ID,
        video_id=video.bunny_video_id
    )

    try:
        with httpx.Client() as client:
            lang_post_maps = {}

            # Process each supported language
            for lang in BigLanguage:
                # Find translation for this language
                translation = None
                for trans in video.meta_translations:
                    if trans["lang"] == lang.short_code:
                        translation = trans
                        break

                if not translation:
                    logger.warning(f"No translation found for language {lang.short_code}, skipping...")
                    continue

                all_categories = list(set(translation["categories"] + [video.keyword]))

                post = create_post(
                    client=client,
                    title=translation["title"],
                    content=video_embed,
                    description=translation["description"],
                    tags=translation["tags"],  # todo: use translated one
                    categories=all_categories,  # todo: use translated one
                    lang=lang.short_code,
                    image_url=f"https://{BUNNY_CDN_DOMAIN}/{video.bunny_video_id}/thumbnail.jpg"
                )

                lang_post_maps[lang.short_code] = post["id"]
                logger.info(f"✅ [{lang.short_code}] post created with ID: {post['id']} "
                            f"with {len(translation['tags'])} tags and {len(all_categories)} categories "
                            f"(including {len(video.keyword)} keyword)")

            # Link the posts in different languages
            if len(lang_post_maps) > 1:
                link_result = link_posts(client, lang_post_maps)
                logger.info(f"✅ Posts linked: {link_result}")

            return True, ""
    except Exception as e:
        logger.error(f"Failed to publish video: {str(e)}")
        traceback.print_exc()
        return False, str(e)


def process_pending_videos():
    with Session(engine) as session:
        # Only process videos that have been meta translated
        pending_videos = session.query(Video).filter(
            Video.status == VideoStatus.meta_translated
        ).all()

        for video in pending_videos:
            if not video.meta_translations:
                logger.warning(f"Video {video.id} has no translations, skipping...")
                continue

            success, error = publish_video_to_wordpress(video)
            if success:
                video.status = VideoStatus.published
                logger.info(f"Successfully published video {video.id}")
            else:
                video.status = VideoStatus.failed_published
                video.failed_reason = error[:1000]
                logger.error(f"Failed to publish video {video.id}: {error}")

            session.commit()


if __name__ == "__main__":
    init_logging("publish")
    process_pending_videos()
