import re
from base64 import b64encode
from typing import List, Dict
from urllib.parse import urlparse

import httpx

from src.lib.config import WP_BASE_URL, WP_USERNAME, WP_PASSWORD, BUNNY_CDN_DOMAIN, BUNNY_LIBRARY_ID, WP_DEFAULT_USER_ID
from src.lib.consts import VIDEO_EMBED_TEMPLATE
from src.lib.enums import Language
from src.lib.models import Video
from src.lib.schemas import TaxonomyIn
from src.utils.string_utils import hash_to_base62

WP_API_URL = f"{WP_BASE_URL}/wp-json/wp/v2"
CREDENTIALS = b64encode(f"{WP_USERNAME}:{WP_PASSWORD}".encode()).decode("utf-8")
HEADERS = {
    "Authorization": f"Basic {CREDENTIALS}",
    "Content-Type": "application/json"
}


def wp_link_posts(link_maps: dict) -> Dict:
    with httpx.Client() as client:
        response = client.post(
            f"{WP_BASE_URL}/wp-json/custom/v1/link-posts",
            json=link_maps,
            headers=HEADERS
        )
        response.raise_for_status()
        return response.json()


def wp_create_post(video: Video, author_id, lang: Language, tag_ids: List[int], category_ids: List[int]) -> dict:
    assert BUNNY_LIBRARY_ID and video.bunny_video_id, "Bunny library ID and video ID not set"
    video_embed = VIDEO_EMBED_TEMPLATE.format(
        library_id=BUNNY_LIBRARY_ID,
        video_id=video.bunny_video_id
    )
    data = {
        "title": video.title_translations.get(lang.short_code, video.title),
        "content": video_embed,
        "status": "publish",
        "lang": lang.short_code,
        "tags": tag_ids,
        "categories": category_ids,
        "author": author_id,
        "meta": {
            "_harikrutfiwu_url": f"https://{BUNNY_CDN_DOMAIN}/{video.bunny_video_id}/thumbnail.jpg",
            "_harikrutfiwu_alt": video.title
        }
    }

    with httpx.Client() as client:
        response = client.post(f"{WP_API_URL}/posts", json=data, headers=HEADERS)
        response.raise_for_status()
        return response.json()


def wp_batch_get_or_add_terms(data: TaxonomyIn) -> Dict[str, List[int]]:
    if len(data.translations) == 0:
        return {}
    with httpx.Client() as client:
        response = client.post(
            f"{WP_BASE_URL}/wp-json/custom/v1/import-translated-terms",
            json=data.model_dump(),
            headers=HEADERS,
            timeout=30
        )
        response.raise_for_status()
        return response.json()


def is_valid_username(s):
    return re.fullmatch(r'[a-zA-Z0-9_]', s) is not None


def wp_get_or_create_user(author_name, author_url) -> int:
    if not author_name.strip() or not author_url.strip():
        return WP_DEFAULT_USER_ID

    parts = urlparse(author_url)
    username = re.sub(r"\W+", "_", author_name.strip().lower())
    if not is_valid_username(username):
        username = hash_to_base62(username)

    payload = {
        "username": f"{username}_{parts.netloc}".replace(".", "_"),
        "email": f"{username}@{parts.netloc}",
        "name": author_name
    }

    with httpx.Client() as client:
        response = client.post(
            f"{WP_BASE_URL}/wp-json/custom/v1/get_or_create_user",
            json=payload,
            headers=HEADERS,
        )
        response.raise_for_status()
        return response.json()["id"]
