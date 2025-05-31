import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict

from loguru import logger
from sqlalchemy.orm import Session

from src.lib.connection import engine
from src.lib.consts import VideoStatus, BigLanguage, DB_ERROR_LOG_LENGTH
from src.lib.models import Video
from src.utils.google_translate_utils import translate_video_content
from src.utils.log_utils import init_logging


def translate_content_for_language(content: dict, lang: BigLanguage) -> tuple[BigLanguage, dict]:
    """Translate all content to a specific language"""
    try:
        translated = translate_video_content(content, lang)
        return lang, translated
    except Exception as e:
        logger.error(f"Failed to translate to {lang.short_code}: {str(e)}")
        traceback.print_exc()
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
                    "tags": translated_content["tags"],
                    "categories": translated_content["categories"]
                })
            except Exception as e:
                failed_languages.append(lang)
                logger.error(f"Translation failed for {lang.long_code}: {str(e)}")
                traceback.print_exc()

    if failed_languages:
        failed_langs = ", ".join(lang.long_code for lang in failed_languages)
        raise Exception(f"Translation failed for languages: {failed_langs}")

    return translations


def process_video_batch(video_batch: List[Video], languages: List[BigLanguage]) -> tuple[int, int]:
    """Process a batch of videos for translation"""
    success_count = 0
    fail_count = 0

    with Session(engine) as session:
        for video in video_batch:
            try:
                # Prepare content for translation
                content = {
                    "title": video.downloaded_title or video.title,
                    "tags": video.downloaded_tags,
                    "categories": video.downloaded_categories
                }

                # Get translations for all languages
                translations = translate_content_concurrent(content, languages)

                # Update video with translations and status
                video.meta_translations = translations
                video.status = VideoStatus.meta_translated
                success_count += 1
                logger.info(f"Successfully translated video {video.id}")
            except Exception as e:
                error_msg = f"Content translation failed: {str(e)}"
                logger.error(f"Error processing video {video.id}: {error_msg}")
                video.status = VideoStatus.failed_meta_translated
                video.failed_reason = error_msg[:DB_ERROR_LOG_LENGTH]
                fail_count += 1
                traceback.print_exc()

        # Commit all changes for the batch
        session.commit()

    return success_count, fail_count


def process_all_pending_videos(batch_size: int = 10):
    """Process all pending videos in batches using last_id for pagination"""
    total_success = 0
    total_failed = 0
    batch_number = 0
    last_id = 0

    # Get list of languages to translate to (excluding English)
    languages = [lang for lang in BigLanguage if lang != BigLanguage.ENGLISH]

    while True:
        with Session(engine) as session:
            # Get next batch of videos using last_id
            pending_videos = session.query(Video).filter(
                Video.status == VideoStatus.subtitled,
                Video.id > last_id
            ).order_by(Video.id.asc()).limit(batch_size).all()

            if not pending_videos:
                break

            batch_number += 1
            batch_count = len(pending_videos)
            last_id = pending_videos[-1].id  # Update last_id to the last video in current batch

            logger.info(
                f"Processing batch {batch_number} with {batch_count} videos (IDs {pending_videos[0].id} to {pending_videos[-1].id})")

        # Process the batch (with a new session)
        success_count, fail_count = process_video_batch(pending_videos, languages)
        total_success += success_count
        total_failed += fail_count

        logger.info(
            f"Batch {batch_number} completed: {success_count} succeeded, {fail_count} failed (last_id: {last_id})")

    total_processed = total_success + total_failed
    if total_processed == 0:
        logger.info("No pending videos found for translation")
        return

    logger.info("Translation processing completed:")
    logger.info(f"- Total batches processed: {batch_number}")
    logger.info(f"- Total videos processed: {total_processed}")
    logger.info(f"- Successfully translated: {total_success}")
    logger.info(f"- Failed: {total_failed}")
    logger.info(f"- Last processed ID: {last_id}")


if __name__ == "__main__":
    init_logging("translate_title")
    process_all_pending_videos()
