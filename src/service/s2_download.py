import asyncio
import sys
import time
import traceback
from concurrent.futures import ProcessPoolExecutor

from loguru import logger
from yt_dlp.utils import DownloadError, RegexNotFoundError

from src.crud.video_crud import VideoCrud
from src.lib.config import MAX_ACCEPT_VIDEO_SIZE
from src.lib.consts import WEBSITES
from src.lib.models import VideoStatus
from src.utils.download_utils import download_remote_video, SizeLimitExceeded, to_mb
from src.utils.file_utils import rm_video
from src.utils.log_utils import init_logging


def download_videos(batch_size: int = 10, host: str = ""):
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.fetched, host)
        if not videos:
            logger.info("All downloaded, sleeping for 1 hour")
            time.sleep(1 * 60 * 60)
            continue

        last_id = videos[-1].id
        for video in videos:
            logger.info(f"[{video.id} | {video.host} | {video.original_id}] download started")

            try:
                video_filename, info = download_remote_video(video.url, video.path.parent)
                filesize = video.path.parent.joinpath(video_filename).stat().st_size
                VideoCrud.update({
                    "id": video.id,
                    "status": VideoStatus.downloaded,
                    "filename": video_filename,
                    "title": info.get("title", video.title),
                    "tags": info.get("tags", []),
                    "categories": info.get("categories", []),
                    "duration": int(info.get("duration", 0)),
                    "file_size": filesize,
                    "width": info.get("width", 0),
                    "height": info.get("height", 0),
                    "aspect_ratio": info.get("aspect_ratio", 0.0),
                })

                if video.file_size > MAX_ACCEPT_VIDEO_SIZE:
                    reason = VideoCrud.update_status(video.id, VideoStatus.failed,
                                                     VideoStatus.converted.log(
                                                         f"Video large than {to_mb(MAX_ACCEPT_VIDEO_SIZE)}MB."))
                    logger.warning(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
                else:
                    logger.info(f"[{video.id} | {video.host} | {video.original_id}]  Downloaded")
            except (SizeLimitExceeded, DownloadError, RegexNotFoundError) as e:
                VideoCrud.update_status(video.id, VideoStatus.failed, VideoStatus.downloaded.log(e))
                asyncio.run(rm_video(video))
                logger.warning(str(e))
            except Exception as e:
                VideoCrud.update_status(video.id, VideoStatus.failed, VideoStatus.downloaded.log(e))
                asyncio.run(rm_video(video))
                exception_count += 1
                if exception_count >= 3:
                    raise e
                traceback.print_exc()


def download_websites(batch_size: int = 10, host: str = ""):
    logger.info(f"[{host if host else 'All'}] download started")

    if host:
        download_videos(batch_size, host)
        return

    with ProcessPoolExecutor(max_workers=batch_size) as executor:
        futures = []
        for h in WEBSITES.keys():
            futures.append(executor.submit(download_videos, batch_size, h))

        for future in futures:
            future.result()


if __name__ == "__main__":
    init_logging("download")

    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 2
    host = sys.argv[2] if len(sys.argv) > 2 else ""

    download_websites(batch_size, host)
    logger.info("All downloaded")
