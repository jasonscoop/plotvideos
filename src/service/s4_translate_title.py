from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from loguru import logger
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.lib.connection import engine
from src.lib.consts import VideoStatus, BigLanguage, DB_ERROR_LOG_LENGTH
from src.lib.models import Video
from src.utils.llm_utils import translate_video_content


def translate_content_for_language(content: dict, lang: BigLanguage) -> tuple[BigLanguage, dict]:
    """Translate all content to a specific language"""
    try:
        translated = translate_video_content(content, lang)
        return lang, translated
    except Exception as e:
        logger.error(f"Failed to translate to {lang.full_name}: {str(e)}")
        raise


def translate_content_concurrent(content: dict, languages: List[BigLanguage], max_workers: int = 5) -> Dict:
    """Translate all content to multiple languages concurrently"""
    translations = []
    failed_languages = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all translation tasks
        future_to_lang = {
            executor.submit(translate_content_for_language, content, lang): lang
            for lang in languages
        }

        # Process completed translations
        for future in as_completed(future_to_lang):
            lang = future_to_lang[future]
            try:
                result_lang, translated_content = future.result()
                # Store translations by language code
                translations.append({
                    "lang": result_lang.short_code,
                    "title": translated_content["title"],
                    "description": translated_content["description"],
                    "tags": translated_content["tags"],
                    "categories": translated_content["categories"]
                })
            except Exception as e:
                failed_languages.append(lang)
                logger.error(f"Translation failed for {lang.full_name}: {str(e)}")

    if failed_languages:
        failed_langs = ", ".join(lang.full_name for lang in failed_languages)
        raise Exception(f"Translation failed for languages: {failed_langs}")

    return translations


def process_video_content_translation(video_id: int) -> None:
    with Session(engine) as session:
        # Get the video
        stmt = select(Video).where(Video.id == video_id)
        video = session.execute(stmt).scalar_one_or_none()

        if not video:
            logger.error(f"Video {video_id} not found")
            return

        try:
            # Prepare content for translation
            content = {
                "title": video.downloaded_title or video.title,
                "description": video.downloaded_description,
                "tags": video.downloaded_tags,
                "categories": video.downloaded_categories
            }

            # Get list of languages to translate to (excluding English)
            languages = [lang for lang in BigLanguage if lang != BigLanguage.ENGLISH]

            # Get translations for all languages
            translations = translate_content_concurrent(content, languages)

            # Update video with translations and status
            video.title_translations = translations
            video.status = VideoStatus.meta_translated
            session.commit()

            logger.info(f"Successfully translated all content for video {video_id} to {len(languages)} languages")

        except Exception as e:
            logger.error(f"Error processing video {video_id}: {str(e)}")
            video.status = VideoStatus.meta_translate_failed
            video.failed_reason = f"Content translation failed: {str(e)}"[:DB_ERROR_LOG_LENGTH]
            session.commit()


def process_all_pending_videos():
    """Process all videos that need translation from the database."""
    with Session(engine) as session:
        # Get all videos that are downloaded but not translated
        pending_videos = session.query(Video).filter(
            Video.status == VideoStatus.downloaded
        ).all()

        total_videos = len(pending_videos)
        if total_videos == 0:
            logger.info("No pending videos found for translation")
            return

        logger.info(f"Found {total_videos} videos pending translation")
        
        success_count = 0
        fail_count = 0

        for index, video in enumerate(pending_videos, 1):
            try:
                logger.info(f"Processing video {video.id} ({index}/{total_videos})")
                process_video_content_translation(video.id)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to process video {video.id}: {str(e)}")
                fail_count += 1
                continue

        logger.info(f"Translation processing completed:")
        logger.info(f"- Total videos: {total_videos}")
        logger.info(f"- Successfully translated: {success_count}")
        logger.info(f"- Failed: {fail_count}")


if __name__ == "__main__":
    # For testing
    import sys

    if len(sys.argv) > 1:
        video_id = int(sys.argv[1])
        process_video_content_translation(video_id)
    else:
        # If no video ID is provided, process all pending videos
        logger.info("No video ID provided, processing all pending videos...")
        process_all_pending_videos()
