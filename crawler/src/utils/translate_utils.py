import time
from typing import List

import requests
from loguru import logger
from tenacity import stop_after_attempt, retry, wait_random

from core.config import (
    RAPIDAPI_AI_TRANSLATE_KEY_URL,
    RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL,
    RAPIDAPI_TRANSLATE_FALLBACK_DELAY_SEC,
    RAPIDAPI_TRANSLATE_MIN_INTERVAL_SEC,
)
from core.languages import Language

_API_KEY_TTL = 3600
_api_key_cache: dict[str, tuple[str, float]] = {}
_last_translate_request_mono: float = 0.0


def _throttle_translate_request() -> None:
    global _last_translate_request_mono
    interval = RAPIDAPI_TRANSLATE_MIN_INTERVAL_SEC
    if interval <= 0:
        return
    now = time.monotonic()
    wait = interval - (now - _last_translate_request_mono)
    if wait > 0:
        time.sleep(wait)
    _last_translate_request_mono = time.monotonic()


def _fetch_api_key(url: str) -> str:
    now = time.monotonic()
    if url in _api_key_cache:
        key, expires_at = _api_key_cache[url]
        if now < expires_at:
            return key
    key = requests.get(url, timeout=10).text.strip()
    _api_key_cache[url] = (key, now + _API_KEY_TTL)
    return key


def translate_list(texts: List[str], lang: Language) -> List[str]:
    try:
        return _translate_via_ai(texts, lang)
    except Exception as e:
        if not RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL.strip():
            logger.error(
                f"translate_via_ai failed for '{lang.code}': {e}; "
                "RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL is not set (required for fallback when primary fails)"
            )
            raise RuntimeError(
                f"translate_via_ai failed ({e!s}); "
                "set RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL for fallback"
            ) from e
        logger.warning(f"translate_via_ai failed for '{lang.code}': {e}, falling back")
        fd = RAPIDAPI_TRANSLATE_FALLBACK_DELAY_SEC
        if fd > 0:
            time.sleep(fd)
        return _translate_via_google(texts, lang)


@retry(wait=wait_random(2, 5), stop=stop_after_attempt(3), reraise=True)
def _translate_via_ai(texts: List[str], lang: Language) -> List[str]:
    if not RAPIDAPI_AI_TRANSLATE_KEY_URL.strip():
        raise RuntimeError("RAPIDAPI_AI_TRANSLATE_KEY_URL is not set")

    payload = {"texts": texts, "tl": lang.code, "sl": "auto"}
    headers = {
        "x-rapidapi-key": _fetch_api_key(RAPIDAPI_AI_TRANSLATE_KEY_URL),
        "Content-Type": "application/json",
    }

    _throttle_translate_request()
    response = requests.post(
        "https://ai-translate.p.rapidapi.com/translateHtml",
        json=payload, headers=headers, timeout=60,
    )
    response.raise_for_status()
    return response.json()["data"][0]


@retry(wait=wait_random(3, 7), stop=stop_after_attempt(3), reraise=True)
def _translate_via_google(texts: List[str], lang: Language) -> List[str]:
    if not RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL.strip():
        raise RuntimeError("RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL is not set")

    payload = {"from": "auto", "to": lang.code, "json": texts}
    headers = {
        "x-rapidapi-key": _fetch_api_key(RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL),
        "Content-Type": "application/json",
    }

    _throttle_translate_request()
    response = requests.post(
        "https://google-translate113.p.rapidapi.com/api/v1/translator/json",
        json=payload, headers=headers, timeout=60,
    )
    response.raise_for_status()
    return response.json()["trans"]
