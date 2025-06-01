import traceback
from typing import List, Dict

from loguru import logger
from sqlalchemy.orm import Session

from src.lib.connection import engine
from src.lib.consts import VideoStatus, BigLanguage, DB_ERROR_LOG_LENGTH
from src.lib.models import Video
from src.utils.log_utils import init_logging
from src.utils.translate_utils import translate_texts


def translate_video_content(content: dict, lang: BigLanguage) -> dict:
    """Translate video content to a specific language"""
    try:
        # Prepare texts to translate
        texts_to_translate = [
            content["title"],
            *content["tags"],
            *content["categories"]
        ]
        
        # Translate all texts at once
        translated_texts = translate_texts(texts_to_translate, lang)
        
        # Split translated texts back into title, tags, and categories
        translated_title = translated_texts[0]
        translated_tags = translated_texts[1:1+len(content["tags"])]
        translated_categories = translated_texts[1+len(content["tags"]):]
        
        return {
            "title": translated_title,
            "tags": translated_tags,
            "categories": translated_categories
        }
    except Exception as e:
        logger.error(f"Translation failed for {lang.short_code}: {str(e)}")
        raise


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

                translations = []
                # Translate for each language sequentially
                for lang in languages:
                    try:
                        translated_content = translate_video_content(content, lang)
                        translations.append({
                            "lang": lang.short_code,
                            "title": translated_content["title"],
                            "tags": translated_content["tags"],
                            "categories": translated_content["categories"]
                        })
                        logger.info(f"Successfully translated video {video.id} to {lang.long_code}")
                    except Exception as e:
                        logger.error(f"Failed to translate video {video.id} to {lang.long_code}: {str(e)}")
                        raise

                # Update video with translations and status
                video.title_translations = translations
                video.status = VideoStatus.meta_translated
                success_count += 1
                logger.info(f"Successfully translated video {video.id} to all languages")
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
