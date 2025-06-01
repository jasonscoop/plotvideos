from base64 import b64encode
from typing import List, Dict
from urllib.parse import urlparse

import httpx

from src.lib.config import WP_BASE_URL, WP_USERNAME, WP_PASSWORD, BUNNY_CDN_DOMAIN, BUNNY_LIBRARY_ID
from src.lib.consts import BigLanguage, TermType, VIDEO_EMBED_TEMPLATE
from src.lib.models import Video

WP_API_URL = f"{WP_BASE_URL}/wp-json/wp/v2"
CREDENTIALS = b64encode(f"{WP_USERNAME}:{WP_PASSWORD}".encode()).decode("utf-8")
HEADERS = {
    "Authorization": f"Basic {CREDENTIALS}",
    "Content-Type": "application/json"
}


def wp_parse_lang(url: str) -> BigLanguage:
    path = urlparse(url).path
    parts = path.strip('/').split('/')
    if len(parts) == 0 or len(parts[0]) != 2:
        return BigLanguage.ENGLISH

    return BigLanguage.from_short_code(parts[0])


def wp_get_terms_lang_map_id(search: str, term_type: TermType, per_page=1) -> dict:
    results = wp_get_terms(search, term_type, per_page)
    return {wp_parse_lang(r["link"]): r["id"] for r in results}


def wp_get_terms(search: str, term_type: TermType, per_page=1):
    with httpx.Client() as client:
        params = {
            "search": search,
            "per_page": per_page,
        }

        response = client.get(f"{WP_API_URL}/{term_type.value}", params=params)
        response.raise_for_status()
        return response.json()


def wp_create_term(name: str, term_type: TermType, lang: BigLanguage) -> int:
    with httpx.Client() as client:
        response = client.post(
            f"{WP_API_URL}/{term_type.value}",
            json={
                "name": name,
                "lang": lang.short_code,
            },
            headers=HEADERS
        )
        response.raise_for_status()
        return response.json()["id"]


def wp_link_posts(link_maps: dict) -> Dict:
    with httpx.Client() as client:
        response = client.post(
            f"{WP_BASE_URL}/wp-json/custom/v1/link-posts",
            json=link_maps,
            headers=HEADERS
        )
        response.raise_for_status()
        return response.json()


def wp_link_terms(link_maps: dict, taxonomy: TermType) -> Dict:
    with httpx.Client() as client:
        response = client.post(
            f"{WP_BASE_URL}/wp-json/custom/v1/link-terms",
            json={
                "taxonomy": taxonomy.name,
                "translations": link_maps,
            },
            headers=HEADERS
        )
        response.raise_for_status()
        return response.json()


def wp_create_post(video: Video, lang: BigLanguage, tag_ids: List[int], category_ids: List[int]) -> dict:
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
        "meta": {
            "_harikrutfiwu_url": f"https://{BUNNY_CDN_DOMAIN}/{video.bunny_video_id}/thumbnail.jpg",
            "_harikrutfiwu_alt": video.title
        }
    }

    with httpx.Client() as client:
        response = client.post(f"{WP_API_URL}/posts", json=data, headers=HEADERS)
        response.raise_for_status()
        return response.json()
