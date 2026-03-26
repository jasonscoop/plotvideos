import time
from typing import List

import requests
from loguru import logger
from tenacity import stop_after_attempt, retry, wait_random

from core.config import RAPIDAPI_AI_TRANSLATE_KEY_URL, RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL
from core.languages import Language

_API_KEY_TTL = 3600  # 1 hour
_api_key_cache: dict[str, tuple[str, float]] = {}


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
    """Primary translate with fallback. Callers should use this."""
    try:
        return _translate_via_ai(texts, lang)
    except Exception as e:
        logger.warning(f"translate_via_ai failed for '{lang.code}': {e}, falling back")
        return _translate_via_google(texts, lang)


@retry(wait=wait_random(2, 5), stop=stop_after_attempt(3), reraise=True)
def _translate_via_ai(texts: List[str], lang: Language) -> List[str]:
    assert RAPIDAPI_AI_TRANSLATE_KEY_URL, "RAPIDAPI_AI_TRANSLATE_KEY_URL is not set"

    payload = {"texts": texts, "tl": lang.code, "sl": "auto"}
    headers = {
        "x-rapidapi-key": _fetch_api_key(RAPIDAPI_AI_TRANSLATE_KEY_URL),
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://ai-translate.p.rapidapi.com/translateHtml",
        json=payload, headers=headers, timeout=60,
    )
    response.raise_for_status()
    return response.json()["data"][0]


@retry(wait=wait_random(3, 7), stop=stop_after_attempt(3), reraise=True)
def _translate_via_google(texts: List[str], lang: Language) -> List[str]:
    assert RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL, "RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL is not set"

    payload = {"from": "auto", "to": lang.code, "json": texts}
    headers = {
        "x-rapidapi-key": _fetch_api_key(RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL),
        "Content-Type": "application/json",
    }

    response = requests.post(
        "https://google-translate113.p.rapidapi.com/api/v1/translator/json",
        json=payload, headers=headers, timeout=60,
    )
    response.raise_for_status()
    return response.json()["trans"]
