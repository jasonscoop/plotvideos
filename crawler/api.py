from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from crawler.core.config import CRAWLER_API_KEY, B2_CDN_DOMAIN
from crawler.core.enums import VideoStatus
from crawler.core.languages import Language
from crawler.core.models import Video
from crawler.crud.term_crud import TermCrud
from crawler.crud.video_title_translation_crud import TitleTranslationCrud

API_KEY = CRAWLER_API_KEY
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _get_api_key(request: Request) -> str:
    """Rate-limit key: use the API key header value."""
    return request.headers.get("X-API-Key", request.client.host)


limiter = Limiter(key_func=_get_api_key)

app = FastAPI(title="Crawler Pull API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _check_auth(api_key: str = Depends(_api_key_header)) -> str:
    if not API_KEY or api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


@app.get("/videos")
@limiter.limit("60/minute")
def get_videos(
    request: Request,
    after_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    _: str = Depends(_check_auth),
) -> List[dict]:
    languages = Language.get_all()
    videos = _fetch_published(after_id, limit)
    return [_build_payload(v, languages) for v in videos]


def _fetch_published(last_id: Optional[int], limit: int) -> List[Video]:
    from crawler.core.connection import get_db
    with get_db() as session:
        query = session.query(Video).filter(Video.status == VideoStatus.published)
        if last_id is not None:
            query = query.filter(Video.id > last_id)
        return query.order_by(Video.id.asc()).limit(limit).all()


def _build_payload(video: Video, languages: list) -> dict:
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

    cdn = B2_CDN_DOMAIN.rstrip("/")

    subtitle_tracks = [
        {
            "lang": lang.code,
            "label": lang.native_name,
            "url": f"{cdn}/media/{sp.translated_s3_key}{lang.code}.vtt",
        }
        for lang in languages
    ]

    return {
        "original_id": video.id,
        "title": video.title,
        "duration": video.duration,
        "width": video.width,
        "height": video.height,
        "thumbnail_url": f"{cdn}/media/{sp.thumbnail_s3_key}",
        "video_url": f"{cdn}/media/{sp.video_s3_key}",
        "hls_url": f"{cdn}/media/{sp.hls_master_s3_key}",
        "store_dir": video.store_dir,
        "keyword": keyword,
        "tags": tags,
        "categories": categories,
        "translations": translations,
        "subtitle_tracks": subtitle_tracks,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("crawler.api:app", host="0.0.0.0", port=8001)