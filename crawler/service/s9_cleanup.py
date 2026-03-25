from typing import Optional, Tuple

from loguru import logger

from crawler.crud.video_crud import VideoCrud
from crawler.core.config import S7_UPLOAD_BATCH_SIZE
from crawler.core.enums import VideoStatus
from crawler.utils.file_utils import rm_video

_BATCH_SIZE = S7_UPLOAD_BATCH_SIZE


def process_batch(last_id: Optional[int]) -> Tuple[bool, Optional[int]]:
    """Clean local files for one batch of uploaded/failed videos. Returns (had_work, next_last_id)."""
    did_work = False
    next_last_id = last_id

    uploaded = VideoCrud.batch_get(last_id, _BATCH_SIZE, VideoStatus.uploaded)
    if uploaded:
        for video in uploaded:
            rm_video(video)
            logger.info(
                f"[{video.id} | {video.host}] remove all files"
            )
        next_last_id = uploaded[-1].id
        did_work = True

    failed = VideoCrud.get_exceeded_failed(last_id, _BATCH_SIZE)
    if failed:
        for video in failed:
            rm_video(video)
            logger.info(
                f"[{video.id} | {video.host}] remove permanently failed files"
            )
        did_work = True

    return did_work, next_last_id if did_work else None


def clean_files():
    last_id = None
    while True:
        had_work, last_id = process_batch(last_id)
        if not had_work:
            break
