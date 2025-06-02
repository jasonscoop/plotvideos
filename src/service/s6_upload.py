import traceback

from loguru import logger

from src.lib.config import BUNNY_API_KEY, BUNNY_LIBRARY_ID
from src.lib.connection import SessionLocal
from src.lib.consts import VideoStatus, DB_ERROR_LOG_LENGTH, Language
from src.lib.models import Video
from src.lib.schemas import StorePath
from src.utils.bunny_utils import BunnyStreamClient
from src.utils.log_utils import init_logging


def process_translated_videos(batch_size: int = 10):
    """Process videos that have been translated and upload them to Bunny.net"""
    session = SessionLocal()
    bunny_client = BunnyStreamClient(BUNNY_API_KEY, BUNNY_LIBRARY_ID)
    last_id = 0

    try:
        while True:
            videos = (
                session.query(Video)
                .filter(Video.status == VideoStatus.vtt_translated, Video.id > last_id)
                .order_by(Video.id)
                .limit(batch_size)
                .all()
            )
            if not videos:
                break

            logger.info(f"Processing batch of {len(videos)} videos (last_id {last_id})")
            for video in videos:
                logger.info(f"[{video.id}] Uploading video and subtitles for: {video.title}")
                path = StorePath(video.host, video.original_id)

                try:
                    # guid = bunny_client.upload_video(video, path)
                    guid = video.bunny_video_id
                    for lang in Language:
                        vtt_file = path.translated_vtts / f"{lang.short_code}.vtt"
                        if not vtt_file.exists():
                            logger.warning(f"Subtitle file not found: {vtt_file}")
                            continue
                        bunny_client.upload_subtitle(guid, vtt_file, lang)

                    video.status = VideoStatus.uploaded
                    video.bunny_video_id = guid
                    logger.info(f"[{video.id}] Successfully uploaded video and subtitles: {video.title}")
                except Exception as e:
                    video.status = VideoStatus.failed_uploaded
                    video.failed_reason = str(e)[:DB_ERROR_LOG_LENGTH]
                    logger.error(f"Upload failed: {e}")
                    traceback.print_exc()

                session.commit()
            last_id = videos[-1].id
    finally:
        session.close()


if __name__ == '__main__':
    init_logging("upload")
    process_translated_videos()
