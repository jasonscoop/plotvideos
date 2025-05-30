from loguru import logger

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
                logger.info(f"Generating subtitle for: {video.title}")
                try:
                    subtitle_content = generate_subtitle(video)
                    video.subtitle_content = subtitle_content
                    video.status = VideoStatus.subtitled
                    logger.info(f"Generated subtitle successfully for: {video.title}")
                except Exception as e:
                    video.status = VideoStatus.subtitle_failed
                    video.failed_reason = str(e)[:1000]  # Truncate if too long
                    logger.error(f"Failed to generate subtitle: {e}")
                session.commit()
            last_id = videos[-1].id
    finally:
        session.close()


if __name__ == '__main__':
    init_logging("subtitle")
    process_downloaded_videos()
