from typing import Optional, Tuple

from loguru import logger

from crud.video_crud import VideoCrud
from core.config import S7_UPLOAD_BATCH_SIZE
from core.enums import VideoStatus
from utils.file_utils import rm_video

_BATCH_SIZE = S7_UPLOAD_BATCH_SIZE


def process_batch(last_id: Optional[int]) -> Tuple[bool, Optional[int]]:
    """Clean local files for one batch of permanently failed videos. Returns (had_work, next_last_id)."""
    failed = VideoCrud.get_exceeded_failed(last_id, _BATCH_SIZE)
    if not failed:
        return False, None

    for video in failed:
        try:
            rm_video(video)
        except OSError as e:
            logger.warning(f"[{video.id} | {video.host}] rm_video: {e}")
        VideoCrud.update(
            {
                "id": video.id,
                "status": VideoStatus.failed_cleaned,
                "failed_count": 0,
            }
        )
        logger.debug(
            f"[{video.id} | {video.host}] remove permanently failed local files"
        )
    logger.info(
        f"s9_cleanup: cleaned {len(failed)} permanently failed video(s) (status → failed_cleaned)"
    )

    return True, failed[-1].id


def clean_files():
    last_id = None
    while True:
        had_work, last_id = process_batch(last_id)
        if not had_work:
            break
