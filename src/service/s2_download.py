import sys
import traceback
from concurrent.futures import ProcessPoolExecutor

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.consts import DB_ERROR_LOG_LENGTH, WEBSITES
from src.lib.models import VideoStatus
from src.lib.schemas import StorePath
from src.utils.download_utils import download_remote_video, SizeLimitExceeded
from src.utils.log_utils import init_logging


def download_videos(batch_size: int = 10, host: str = ""):
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.fetched, host)
        if not videos:
            break

        last_id = videos[-1].id

        for video in videos:
            logger.info(f"[{video.id} | {video.host} | {video.original_id}] download started")
            path = StorePath(video.host, video.original_id)

            try:
                video_filename, info = download_remote_video(video.url, path.parent)
                VideoCrud.update({
                    "id": video.id,
                    "status": VideoStatus.downloaded,
                    "filename": video_filename,
                    "title": info.get("title", video.title),
                    "tags": info.get("tags", []),
                    "categories": info.get("categories", []),
                    "duration": int(info.get("duration", 0)),
                    "file_size": path.parent.joinpath(video_filename).stat().st_size,
                    "width": info.get("width", 0),
                    "height": info.get("height", 0),
                    "aspect_ratio": info.get("aspect_ratio", 0.0),
                })
                logger.info(f"[{video.id} | {video.host} | {video.original_id}]  Downloaded")
            except SizeLimitExceeded as e:
                reason = str(e)[:DB_ERROR_LOG_LENGTH]
                VideoCrud.update_status(video.id, VideoStatus.skipped_due_to_size, reason)
                logger.warning(str(e))
            except Exception as e:
                reason = str(e)[:DB_ERROR_LOG_LENGTH]
                VideoCrud.update_status(video.id, VideoStatus.failed_downloaded, reason)
                exception_count += 1
                if exception_count >= 3:
                    raise e
                traceback.print_exc()


def download_websites(batch_size: int = 10, host: str = ""):
    logger.info(f"[{host if host else 'All'}] download started")

    if host:
        download_videos(batch_size, host)
        return

    with ProcessPoolExecutor(max_workers=len(WEBSITES)) as executor:
        futures = []
        for h in WEBSITES.keys():
            futures.append(executor.submit(download_videos, batch_size, h))

        for future in futures:
            future.result()


if __name__ == "__main__":
    init_logging("download")

    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    host = sys.argv[2] if len(sys.argv) > 2 else ""

    download_websites(batch_size, host)
    logger.info("All downloaded")
