import time
import traceback
from typing import Optional, Tuple

from loguru import logger

from crud.video_crud import VideoCrud
from core.config import MIN_ACCEPT_DURATION, S3_CONVERT_BATCH_SIZE
from core.models import VideoStatus
from utils.file_utils import rm_video
from utils.media_utils import get_video_duration, media_to_wav
from utils.signal_utils import setup_graceful_shutdown, should_stop


def convert_video(video):
    video_path = video.store_path.video
    if not video_path.exists():
        reason = VideoCrud.record_failure(
            video.id,
            VideoStatus.converted.log(f"Video file {video_path} not found."),
        )
        logger.warning(f"[{video.id} | {video.host}] {reason}")
        return

    duration = video.duration
    if duration == 0:
        duration = get_video_duration(video_path)

    if duration < MIN_ACCEPT_DURATION:
        reason = VideoCrud.record_failure(
            video.id,
            VideoStatus.converted.log(
                f"Duration is shorter than {MIN_ACCEPT_DURATION}s"
            ),
        )
        logger.warning(f"[{video.id} | {video.host}] {reason}")
        return

    media_to_wav(video_path, video.store_path.audio)
    VideoCrud.update(
        {
            "id": video.id,
            "duration": duration,
            "status": VideoStatus.converted,
            "failed_reason": "",
        }
    )
    logger.info(f"[{video.id} | {video.host}] converted to audio")


def process_batch(last_id: Optional[int]) -> Tuple[bool, Optional[int]]:
    """Convert one batch of downloaded videos to WAV. Returns (had_work, next_last_id)."""
    videos = VideoCrud.batch_get(last_id, S3_CONVERT_BATCH_SIZE, VideoStatus.downloaded)
    if not videos:
        return False, None

    exception_count = 0
    for video in videos:
        try:
            convert_video(video)
        except Exception as e:
            VideoCrud.record_failure(video.id, VideoStatus.converted.log(str(e)))
            exception_count += 1
            traceback.print_exc()
            if exception_count > 3:
                raise

    return True, videos[-1].id


def convert_videos():
    setup_graceful_shutdown()
    last_id = None

    while not should_stop():
        had_work, last_id = process_batch(last_id)
        if not had_work:
            logger.info("All converted, sleeping for 10 minutes")
            time.sleep(10 * 60)
            last_id = None
