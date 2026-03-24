import time
from typing import Optional, Tuple

from loguru import logger

from crawler.crud.video_crud import VideoCrud
from crawler.core.config import S7_UPLOAD_BATCH_SIZE
from crawler.core.enums import VideoStatus
from crawler.utils.signal_utils import setup_graceful_shutdown, should_stop


def process_batch(last_id: Optional[int]) -> Tuple[bool, Optional[int]]:
    """Mark one batch of uploaded videos as published. Returns (had_work, next_last_id)."""
    videos = VideoCrud.batch_get(last_id, S7_UPLOAD_BATCH_SIZE, VideoStatus.uploaded)
    if not videos:
        return False, None

    for video in videos:
        VideoCrud.update_status(video.id, VideoStatus.published)
        logger.info(f"[{video.id} | {video.host} | {video.original_id}] marked as published")

    return True, videos[-1].id


def publish_videos():
    setup_graceful_shutdown()
    last_id = None
    while not should_stop():
        had_work, last_id = process_batch(last_id)
        if not had_work:
            logger.info("No uploaded videos to publish, sleeping 5 min")
            time.sleep(5 * 60)
            last_id = None
