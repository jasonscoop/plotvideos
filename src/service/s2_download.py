import traceback

from loguru import logger

from src.lib.connection import SessionLocal
from src.lib.consts import DB_ERROR_LOG_LENGTH
from src.lib.models import Video, VideoStatus
from src.lib.schemas import StorePath
from src.utils.download_utils import download_remote_video
from src.utils.log_utils import init_logging


def download_videos(batch_size: int = 10):
    session = SessionLocal()
    last_id = 0

    try:
        while True:
            videos = (
                session.query(Video)
                .filter(Video.status == VideoStatus.fetched, Video.id > last_id)
                .order_by(Video.id)
                .limit(batch_size)
                .all()
            )
            if not videos:
                break

            logger.info(f"Processing batch of {len(videos)} videos (last_id {last_id})")
            for video in videos:
                logger.info(f"Downloading: {video.title} ({video.url})")
                path = StorePath(video.host, video.original_id)

                try:
                    video_filename, info = download_remote_video(video.url, path.parent)

                    video.status = VideoStatus.downloaded
                    video.filename = video_filename
                    video.tags = info.get("tags", [])
                    video.categories = info.get("categories", [])
                    video.duration = info.get("duration", 0)
                    video.file_size = path.parent.joinpath(video_filename).stat().st_size
                    logger.info(f"Downloaded successfully: {video.title}")
                except Exception as e:
                    video.status = VideoStatus.failed_downloaded
                    video.failed_reason = str(e)[:DB_ERROR_LOG_LENGTH]  # Truncate if too long
                    logger.error(f"Download failed: {e}")
                    traceback.print_exc()
                session.commit()
            last_id = videos[-1].id
    finally:
        session.close()


if __name__ == "__main__":
    init_logging("download")
    download_videos()
    logger.info("All done!")
