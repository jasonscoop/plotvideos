from typing import List

import requests
from tenacity import stop_after_attempt, retry, wait_fixed

from src.lib.config import RAPIDAPI_AI_TRANSLATE_KEY_URL, RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL
from src.lib.models import Language


@retry(wait=wait_fixed(2), stop=stop_after_attempt(3), reraise=True)
def translate_texts1(texts: List[str], lang: Language) -> List[str]:
    assert RAPIDAPI_AI_TRANSLATE_KEY_URL, "Please set the RAPIDAPI_AI_TRANSLATE_KEY_URL environment variable"

    url = "https://ai-translate.p.rapidapi.com/translateHtml"

    payload = {
        "texts": texts,
        "tl": lang.code,
        "sl": "auto"
    }
    headers = {
        "x-rapidapi-key": requests.get(RAPIDAPI_AI_TRANSLATE_KEY_URL).text.strip(),
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    return response.json()["data"][0]


@retry(wait=wait_fixed(2), stop=stop_after_attempt(3), reraise=True)
def translate_texts2(texts: List[str], lang: Language) -> List[str]:
    assert RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL, "Please set the RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL environment variable"

    url = "https://google-translate113.p.rapidapi.com/api/v1/translator/json"
    payload = {
        "from": "auto",
        "to": lang.code,
        "json": texts
    }
    headers = {
        "x-rapidapi-key": requests.get(RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL).text.strip(),
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=60)
    response.raise_for_status()
    return response.json()["trans"]
