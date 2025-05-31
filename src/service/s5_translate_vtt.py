import traceback

from loguru import logger

from src.lib.connection import SessionLocal
from src.lib.consts import BigLanguage, VideoStatus, DB_ERROR_LOG_LENGTH
from src.lib.models import Video
from src.lib.schemas import StorePath
from src.utils.llm_utils import translate_vtt
from src.utils.log_utils import init_logging


def process_subtitled_videos(batch_size: int = 10):
    """Process videos that have been subtitled but not yet translated"""
    session = SessionLocal()
    last_id = 0

    try:
        while True:
            videos = (
                session.query(Video)
                .filter(Video.status == VideoStatus.meta_translated, Video.id > last_id)
                .order_by(Video.id)
                .limit(batch_size)
                .all()
            )
            if not videos:
                break

            logger.info(f"Processing batch of {len(videos)} videos (last_id {last_id})")
            for video in videos:
                if len(video.subtitle_content.strip()) == 0:
                    logger.warning(f"Video {video.id} has no subtitle, skipping")
                    continue

                logger.info(f"Translating subtitles for: {video.title}")
                path = StorePath(video.host, video.original_id)

                try:
                    # Read the original VTT file
                    vtt_content = path.vtt.read_text()

                    # Create translated_vtts directory if it doesn't exist
                    path.translated_vtts.mkdir(exist_ok=True)

                    # Translate to all supported languages
                    for lang in BigLanguage:
                        translated_vtt = translate_vtt(vtt_content, lang)
                        translated_file = path.translated_vtts / f"{lang.short_code}.vtt"
                        translated_file.write_text(translated_vtt)
                        logger.info(f"[{video.id}] Translated to {lang.full_name} successfully")

                    video.status = VideoStatus.vtt_translated
                    logger.info(f"Translated all languages successfully for: {video.title}")
                except Exception as e:
                    video.status = VideoStatus.failed_vtt_translated
                    video.failed_reason = str(e)[:DB_ERROR_LOG_LENGTH]
                    logger.error(f"Translation failed: {e}")
                    traceback.print_exc()

                session.commit()
            last_id = videos[-1].id
    finally:
        session.close()


if __name__ == '__main__':
    init_logging("translate_vtt")
    process_subtitled_videos()
