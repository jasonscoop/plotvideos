from typing import List

import requests
from tenacity import stop_after_attempt, retry, wait_fixed

from src.lib.config import RAPIDAPI_AI_TRANSLATE_KEY_URL
from src.lib.enums import Language


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), reraise=True)
def translate_texts(texts: List[str], lang: Language):
    assert RAPIDAPI_AI_TRANSLATE_KEY_URL, "Please set the RAPIDAPI_AI_TRANSLATE_KEY_URL environment variable"

    url = "https://ai-translate.p.rapidapi.com/translateHtml"

    payload = {
        "texts": texts,
        "tl": lang.short_code,
        "sl": "auto"
    }
    headers = {
        "x-rapidapi-key": requests.get(RAPIDAPI_AI_TRANSLATE_KEY_URL).text.strip(),
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()["data"][0]
