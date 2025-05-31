import traceback

from loguru import logger

from src.lib.config import MAX_ACCEPT_VIDEO_SIZE
from src.lib.connection import SessionLocal
from src.lib.models import Video, VideoStatus
from src.utils.azure_subtitle_utils import generate_subtitle
from src.utils.log_utils import init_logging


def process_downloaded_videos(batch_size: int = 10):
    session = SessionLocal()
    last_id = 0

    try:
        while True:
            videos = (
                session.query(Video)
                .filter(Video.status == VideoStatus.downloaded, Video.id > last_id)
                .order_by(Video.id)
                .limit(batch_size)
                .all()
            )
            if not videos:
                break

            logger.info(f"Processing batch of {len(videos)} videos (last_id {last_id})")
            for video in videos:
                if video.file_size > MAX_ACCEPT_VIDEO_SIZE:
                    video.status = VideoStatus.skipped_due_to_size
                    video.failed_reason = f"[{video.id}] Video size exceeded: {video.file_size} > {MAX_ACCEPT_VIDEO_SIZE}."
                    logger.info(
                        f"[{video.id}] Video size exceeded: has size {video.file_size}  > {MAX_ACCEPT_VIDEO_SIZE}")
                    session.commit()
                    continue

                logger.info(f"Generating subtitle for: {video.title}")
                try:
                    subtitle_content, duration, pre_detected = generate_subtitle(video)
                    video.subtitle_content = subtitle_content
                    if len(subtitle_content.strip()) == 0:
                        video.status = VideoStatus.skipped_due_to_empty_subtitle
                    video.duration = duration
                    video.pre_detected_result = pre_detected.model_dump()
                    video.status = VideoStatus.subtitled
                    logger.info(f"Generated subtitle successfully for: {video.title}")
                except Exception as e:
                    video.status = VideoStatus.failed_subtitled
                    video.failed_reason = str(e)[:1000]  # Truncate if too long
                    logger.error(f"Failed to generate subtitle: {e}")
                    traceback.print_exc()
                session.commit()
            last_id = videos[-1].id
    finally:
        session.close()


if __name__ == '__main__':
    init_logging("subtitle")
    process_downloaded_videos()
