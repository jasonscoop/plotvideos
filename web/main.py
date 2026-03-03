from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.templating import Jinja2Templates

from web.core.config import B2_CDN_DOMAIN
from web.core.db import get_db
from web.core.enums import VideoStatus
from web.core.models import Language, TitleTranslation, Video


ROOT_DIR = Path(__file__).resolve().parents[1]

templates = Jinja2Templates(directory=str(ROOT_DIR / "web" / "templates"))

app = FastAPI(title="LuckVideos", description="Simple video site powered by crawler DB")


def build_thumbnail_url(video: Video) -> str:
    if video.thumbnail_s3_key:
        return f"{B2_CDN_DOMAIN}/{video.thumbnail_s3_key}"
    if video.thumbnail_url:
        return video.thumbnail_url
    return ""


def build_video_url(video: Video) -> str:
    return f"{B2_CDN_DOMAIN}/{video.video_s3_key}"


def build_subtitle_url(video: Video, lang_code: str) -> str:
    return f"{B2_CDN_DOMAIN}/{video.translated_s3_key}{lang_code}.vtt"


def build_hls_url(video: Video) -> str:
    return f"{B2_CDN_DOMAIN}/{video.hls_master_s3_key}"


@app.get("/", response_class=HTMLResponse)
async def index(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(24, ge=1, le=100),
    q: Optional[str] = Query(None, description="Search by title"),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """
    Home page: paginated grid of published videos, optionally filtered by title.
    """
    base_stmt = select(Video).where(Video.status == VideoStatus.published)

    if q:
        like = f"%{q.strip()}%"
        base_stmt = base_stmt.where(Video.title.ilike(like))

    count_stmt = select(func.count()).select_from(base_stmt.subquery())
    count_result = await db.execute(count_stmt)
    total: int = count_result.scalar_one() or 0

    result = await db.execute(
        base_stmt.order_by(Video.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    videos: List[Video] = result.scalars().all()

    video_items: List[Dict[str, Any]] = []
    for v in videos:
        video_items.append(
            {
                "id": v.id,
                "title": v.title,
                "duration": v.duration,
                "host": v.host,
                "thumbnail_url": build_thumbnail_url(v),
            }
        )

    total_pages = max((total + page_size - 1) // page_size, 1)

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "videos": video_items,
            "page": page,
            "page_size": page_size,
            "total": total,
            "total_pages": total_pages,
            "q": q or "",
        },
    )


@app.get("/videos/{video_id}", response_class=HTMLResponse)
async def watch_video(
    request: Request,
    video_id: str,
    lang: Optional[str] = Query(None, description="Preferred subtitle language code"),
    db: AsyncSession = Depends(get_db),
) -> HTMLResponse:
    """
    Video watch page with player and subtitle tracks.
    """
    video = await db.get(Video, video_id)
    if not video or video.status != VideoStatus.published:
        raise HTTPException(status_code=404, detail="Video not found")

    # Enabled languages for which we may have subtitles
    languages_result = await db.execute(
        select(Language).where(Language.enabled.is_(True))
    )
    languages: List[Language] = languages_result.scalars().all()

    # Title translations (if any)
    translations_result = await db.execute(
        select(TitleTranslation).where(TitleTranslation.video_id == video.id)
    )
    translations = translations_result.scalars().all()
    translation_map: Dict[str, str] = {
        t.lang: t.translated_title for t in translations
    }

    preferred_lang = lang or "en"
    display_title = translation_map.get(preferred_lang, video.title)

    subtitle_tracks: List[Dict[str, str]] = []
    for l in languages:
        track_url = build_subtitle_url(video, l.code)
        subtitle_tracks.append(
            {
                "code": l.code,
                "label": l.native_name,
                "url": track_url,
                "default": l.code == preferred_lang,
            }
        )

    context = {
        "request": request,
        "video": {
            "id": video.id,
            "title": display_title,
            "original_title": video.title,
            "duration": video.duration,
            "host": video.host,
            "author_name": video.author_name,
            "author_url": video.author_url,
            "thumbnail_url": build_thumbnail_url(video),
            "video_url": build_video_url(video),
            "hls_url": build_hls_url(video),
        },
        "subtitle_tracks": subtitle_tracks,
        "preferred_lang": preferred_lang,
    }

    return templates.TemplateResponse("watch.html", context)


@app.get("/healthz")
async def healthz() -> Dict[str, str]:
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web.main:app", host="0.0.0.0", port=8000, reload=True)

