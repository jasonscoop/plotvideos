import json
from typing import List, Dict

from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_fixed

from src.lib.config import GOOGLE_PROJECT_ID, GOOGLE_CREDENTIALS_JSON
from src.lib.consts import BigLanguage

# Initialize Google Cloud Translate client
credentials = service_account.Credentials.from_service_account_info(
    json.loads(GOOGLE_CREDENTIALS_JSON)
) if GOOGLE_CREDENTIALS_JSON else None

translate_client = translate.Client(
    credentials=credentials,
    project=GOOGLE_PROJECT_ID
)


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), reraise=True)
def batch_translate_text(texts: List[str], target_lang: str) -> List[str]:
    """Translate a batch of texts using Google Cloud Translate"""
    try:
        if not texts:
            return []

        # Google Translate can handle batch translation natively
        results = translate_client.translate(
            texts,
            target_language=target_lang,
            source_language='en'  # Assuming source is always English
        )
        
        return [result['translatedText'] for result in results]
    except Exception as e:
        logger.error(f"Translation failed: {str(e)}")
        raise


def translate_video_content(content: dict, language: BigLanguage) -> dict:
    """Translate video content to a specific language"""
    # Prepare lists for batch translation
    texts_to_translate = [
        content["title"],
        *content["tags"],
        *content["categories"]
    ]
    
    # Translate all texts in one batch
    translated_texts = batch_translate_text(
        texts=texts_to_translate,
        target_lang=language.short_code
    )
    
    # Extract translated texts
    translated_title = translated_texts[0]
    translated_tags = translated_texts[1:1+len(content["tags"])]
    translated_categories = translated_texts[1+len(content["tags"]):]
    
    return {
        "title": translated_title,
        "tags": translated_tags,
        "categories": translated_categories
    } 