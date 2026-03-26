from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.security.api_key import APIKeyHeader
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from core.config import CRAWLER_API_KEY, b2_cdn_object_url
from core.enums import VideoStatus
from core.languages import Language
from core.models import Video
from core.path_layout import video_cdn_keys
from crud.term_crud import TermCrud
from crud.video_title_translation_crud import TitleTranslationCrud

API_KEY = CRAWLER_API_KEY
_api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


def _get_api_key(request: Request) -> str:
    return request.headers.get("X-API-Key", request.client.host)


limiter = Limiter(key_func=_get_api_key)

app = FastAPI(title="Crawler Pull API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


def _check_auth(api_key: str = Depends(_api_key_header)) -> str:
    if not API_KEY or api_key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return api_key


@app.get("/languages")
@limiter.limit("60/minute")
def get_languages(
    request: Request,
    _: str = Depends(_check_auth),
) -> List[dict]:
    return [
        {"code": lang.code, "name": lang.native_name, "locale": lang.locale}
        for lang in Language.get_all()
    ]


@app.get("/videos")
@limiter.limit("60/minute")
def get_videos(
    request: Request,
    after_id: Optional[int] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    _: str = Depends(_check_auth),
) -> List[dict]:
    languages = Language.get_all()
    videos = _fetch_uploaded(after_id, limit)
    return [_build_payload(v, languages) for v in videos]


def _fetch_uploaded(last_id: Optional[int], limit: int) -> List[Video]:
    from core.connection import get_db
    with get_db() as session:
        query = session.query(Video).filter(Video.status == VideoStatus.uploaded)
        if last_id is not None:
            query = query.filter(Video.id > last_id)
        return query.order_by(Video.id.asc()).limit(limit).all()


def _build_payload(video: Video, languages: list) -> dict:
    sp = video_cdn_keys(video.id)
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
            "url": b2_cdn_object_url(f"{sp.translated_s3_key}{lang.code}.vtt"),
        }
        for lang in languages
    ]

    return {
        "original_id": video.id,
        "title": video.title,
        "duration": video.duration,
        "width": video.width,
        "height": video.height,
        "thumbnail_url": b2_cdn_object_url(sp.thumbnail_s3_key),
        "video_url": b2_cdn_object_url(sp.video_s3_key),
        "hls_url": b2_cdn_object_url(sp.hls_master_s3_key),
        "keyword": keyword,
        "tags": tags,
        "categories": categories,
        "translations": translations,
        "subtitle_tracks": subtitle_tracks,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8001, reload=True)