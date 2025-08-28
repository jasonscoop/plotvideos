import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger
from yt_dlp.utils import DownloadError, RegexNotFoundError

from src.crud.video_crud import VideoCrud
from src.lib.config import MAX_ACCEPT_VIDEO_SIZE, S2_DOWNLOAD_BATCH_SIZE
from src.lib.enums import ThumbnailStatus
from src.lib.models import VideoStatus, Video
from src.utils.download_utils import (
    download_remote_video,
    SizeLimitExceeded,
    to_mb,
    download_image,
)
from src.utils.file_utils import rm_video


def download_video(video: Video):
    try:
        info = download_remote_video(video.url, video.path)
        thumbnail_status = ThumbnailStatus.downloaded
        if not download_image(video.thumbnail_url, video.thumbnail_path):
            thumbnail_status = ThumbnailStatus.failed
        video_size = video.path.video.stat().st_size

        VideoCrud.update(
            {
                "id": video.id,
                "status": VideoStatus.downloaded,
                "filename": video.path.video.name,
                "title": info.get("title", video.title),
                "tags": info.get("tags", []),
                "categories": info.get("categories", []),
                "duration": int(info.get("duration", 0)),
                "file_size": video_size,
                "width": info.get("width", 0),
                "height": info.get("height", 0),
                "aspect_ratio": info.get("aspect_ratio", 0.0),
                "thumbnail_status": thumbnail_status.value,
            }
        )
        if video_size > MAX_ACCEPT_VIDEO_SIZE:
            reason = VideoCrud.update_status(
                video.id,
                VideoStatus.failed,
                VideoStatus.downloaded.log(
                    f"Video large than {to_mb(MAX_ACCEPT_VIDEO_SIZE)}MB."
                ),
            )
            rm_video(video)
            logger.warning(
                f"[{video.id} | {video.host} | {video.original_id}] {reason}"
            )
        else:
            logger.info(
                f"[{video.id} | {video.host} | {video.original_id}]  Downloaded"
            )
    except (SizeLimitExceeded, DownloadError, RegexNotFoundError) as e:
        VideoCrud.update_status(
            video.id, VideoStatus.failed, VideoStatus.downloaded.log(e)
        )
        rm_video(video)
        logger.warning(str(e))
    except Exception as e:
        VideoCrud.update_status(
            video.id, VideoStatus.failed, VideoStatus.downloaded.log(e)
        )
        rm_video(video)
        traceback.print_exc()
        logger.warning(str(e))
        raise e


def download_videos(host: str = ""):
    last_id = 0
    exception_count = 0
    while True:
        videos = VideoCrud.batch_get(
            last_id, S2_DOWNLOAD_BATCH_SIZE, VideoStatus.fetched, host
        )
        if not videos:
            logger.info("All downloaded, sleeping for 1 hour")
            time.sleep(1 * 60 * 60)
            last_id = 0
            continue

        last_id = videos[-1].id
        with ThreadPoolExecutor(max_workers=len(videos)) as executor:
            futures = [executor.submit(download_video, video) for video in videos]
            for future in as_completed(futures):
                try:
                    future.result()  # This will raise any exceptions that occurred
                except Exception as e:
                    exception_count += 1
                    logger.error(f"Error in download: {str(e)}")
                    if exception_count >= 3:
                        raise e
