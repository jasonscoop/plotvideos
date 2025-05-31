import traceback

from loguru import logger

from src.lib.config import BUNNY_API_KEY, BUNNY_LIBRARY_ID
from src.lib.connection import SessionLocal
from src.lib.consts import VideoStatus, DB_ERROR_LOG_LENGTH
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
                logger.info(f"Uploading video and subtitles for: {video.title}")
                path = StorePath(video.host, video.original_id)
                video_path = path.parent / video.video_filename

                try:
                    # Upload the video file first
                    upload_response = bunny_client.upload_video(video_path, video.title)
                    video_guid = upload_response["guid"]
                    video.bunny_response = upload_response

                    # Upload all translated subtitles
                    for subtitle_file in path.translated_vtts.glob("*.vtt"):
                        # Extract language code from filename (e.g., "en.vtt" -> "en")
                        lang_code = subtitle_file.stem
                        try:
                            bunny_client.upload_subtitle(
                                video_guid,
                                subtitle_file,
                                lang_code,
                                None  # Let Bunny.net use default label
                            )
                            logger.info(f"Uploaded subtitle for language: {lang_code}")
                        except Exception as e:
                            logger.error(f"Failed to upload subtitle for language {lang_code}: {e}")
                            traceback.print_exc()

                    video.status = VideoStatus.uploaded
                    logger.info(f"Successfully uploaded video and subtitles: {video.title}")
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
