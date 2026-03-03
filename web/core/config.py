from __future__ import annotations

from os import getenv

from dotenv import load_dotenv

load_dotenv()


def _make_async_url(sync_url: str) -> str:
    if "+psycopg2" in sync_url:
        return sync_url.replace("+psycopg2", "+asyncpg")
    if sync_url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + sync_url[len("postgresql://") :]
    return sync_url


DB_URL = getenv("DB_URL")
if not DB_URL:
    raise RuntimeError("DB_URL is not set in environment")

# Allow overriding for the web app, but default to async version of DB_URL.
ASYNC_DB_URL = getenv("WEB_DB_URL") or _make_async_url(DB_URL)

B2_CDN_DOMAIN = getenv("B2_CDN_DOMAIN", "https://play.luckvideos.com")

