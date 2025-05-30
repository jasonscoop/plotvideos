from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple
from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.lib.connection import engine
from src.lib.consts import VideoStatus, BigLanguage, DB_ERROR_LOG_LENGTH
from src.lib.models import Video
from src.utils.llm_utils import translate_title


def translate_single_title(title: str, lang: BigLanguage) -> Tuple[BigLanguage, str]:
    """Translate a single title to a specific language"""
    try:
        translated = translate_title(title, lang)
        return lang, translated
    except Exception as e:
        logger.error(f"Failed to translate to {lang.full_name}: {str(e)}")
        raise


def translate_titles_concurrent(title: str, languages: List[BigLanguage], max_workers: int = 5) -> List[Dict[str, str]]:
    """Translate title to multiple languages concurrently"""
    translations = []
    failed_languages = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all translation tasks
        future_to_lang = {
            executor.submit(translate_single_title, title, lang): lang
            for lang in languages
        }

        # Process completed translations
        for future in as_completed(future_to_lang):
            lang = future_to_lang[future]
            try:
                result_lang, translated_title = future.result()
                translations.append({
                    "lang": result_lang.short_code,
                    "title": translated_title
                })
            except Exception as e:
                failed_languages.append(lang)
                logger.error(f"Translation failed for {lang.full_name}: {str(e)}")

    if failed_languages:
        failed_langs = ", ".join(lang.full_name for lang in failed_languages)
        raise Exception(f"Translation failed for languages: {failed_langs}")

    return translations


def process_video_title_translation(video_id: int) -> None:
    with Session(engine) as session:
        # Get the video
        stmt = select(Video).where(Video.id == video_id)
        video = session.execute(stmt).scalar_one_or_none()
        
        if not video:
            logger.error(f"Video {video_id} not found")
            return

        try:
            # Get list of languages to translate to (excluding English)
            languages = [lang for lang in BigLanguage if lang != BigLanguage.ENGLISH]
            
            # Perform concurrent translations
            translations = translate_titles_concurrent(video.title, languages)

            # Update video with translations and status
            video.title_translations = translations
            video.status = VideoStatus.translated
            session.commit()
            
            logger.info(f"Successfully translated title for video {video_id} to {len(translations)} languages")

        except Exception as e:
            logger.error(f"Error processing video {video_id}: {str(e)}")
            video.status = VideoStatus.translate_failed
            video.failed_reason = f"Title translation failed: {str(e)}"[:DB_ERROR_LOG_LENGTH]
            session.commit()


if __name__ == "__main__":
    # For testing
    import sys
    if len(sys.argv) > 1:
        video_id = int(sys.argv[1])
        process_video_title_translation(video_id)
    else:
        print("Please provide a video ID as argument")
