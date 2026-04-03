import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple

from loguru import logger
from yt_dlp.utils import DownloadError, RegexNotFoundError

from crud.video_crud import VideoCrud
from core.config import MAX_ACCEPT_VIDEO_SIZE, S2_DOWNLOAD_BATCH_SIZE
from core.enums import ThumbnailStatus
from core.models import VideoStatus, Video
from utils.download_utils import (
    download_remote_video,
    SizeLimitExceeded,
    to_mb,
    download_image,
)
from utils.file_utils import rm_video


def download_video(video: Video):
    try:
        info = download_remote_video(video.url, video.store_path.video)
        thumbnail_status = ThumbnailStatus.downloaded
        if not download_image(video.thumbnail_url, video.store_path.thumbnail):
            thumbnail_status = ThumbnailStatus.failed

        if thumbnail_status == ThumbnailStatus.failed:
            thumbnails = info.get("thumbnails", [])
            if thumbnails and thumbnails[0].get("url"):
                thumbnail_status = ThumbnailStatus.ytdlp_downloaded
                ytdlp_thumbnail_url = thumbnails[0].get("url")
                if not download_image(ytdlp_thumbnail_url, video.store_path.thumbnail):
                    thumbnail_status = ThumbnailStatus.failed

        video_size = video.store_path.video.stat().st_size

        VideoCrud.update(
            {
                "id": video.id,
                "status": VideoStatus.downloaded,
                "filename": video.store_path.video.name,
                "title": info.get("title", video.title),
                "tags": info.get("tags", []),
                "categories": info.get("categories", []),
                "duration": int(info.get("duration", 0)),
                "file_size": video_size,
                "width": info.get("width", 0),
                "height": info.get("height", 0),
                "aspect_ratio": info.get("aspect_ratio", 0.0),
                "thumbnail_url": (
                    ytdlp_thumbnail_url
                    if thumbnail_status == ThumbnailStatus.ytdlp_downloaded
                    else video.thumbnail_url
                ),
                "thumbnail_status": thumbnail_status.value,
            }
        )
        if video_size > MAX_ACCEPT_VIDEO_SIZE:
            VideoCrud.update({"id": video.id, "status": VideoStatus.oversized})
            logger.warning(
                f"[{video.id} | {video.host}] "
                f"Video oversized: {to_mb(video_size)}MB > {to_mb(MAX_ACCEPT_VIDEO_SIZE)}MB"
            )
            rm_video(video)
        else:
            logger.info(
                f"[{video.id} | {video.host}]  Downloaded"
            )
    except SizeLimitExceeded as e:
        reason = VideoStatus.downloaded.log(e)
        try:
            rm_video(video)
        except OSError:
            pass
        VideoCrud.update_status(video.id, VideoStatus.oversized, reason)
        logger.warning(
            f"[{video.id} | {video.host}] Oversized (early abort): {e}"
        )
    except (DownloadError, RegexNotFoundError) as e:
        VideoCrud.record_failure(video.id, VideoStatus.downloaded.log(e))
        logger.warning(str(e))
    except Exception as e:
        VideoCrud.record_failure(video.id, VideoStatus.downloaded.log(e))
        traceback.print_exc()
        logger.warning(str(e))
        raise e


def process_batch(last_id: Optional[int]) -> Tuple[bool, Optional[int]]:
    """Download one batch of fetched videos. Returns (had_work, next_last_id)."""
    videos = VideoCrud.batch_get(last_id, S2_DOWNLOAD_BATCH_SIZE, VideoStatus.fetched)
    if not videos:
        return False, None

    exception_count = 0
    with ThreadPoolExecutor(max_workers=len(videos)) as executor:
        futures = [executor.submit(download_video, video) for video in videos]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                exception_count += 1
                logger.error(f"Error in download: {str(e)}")
                if exception_count >= 3:
                    raise e

    return True, videos[-1].id


def download_videos():
    last_id = None
    while True:
        had_work, last_id = process_batch(last_id)
        if not had_work:
            break
