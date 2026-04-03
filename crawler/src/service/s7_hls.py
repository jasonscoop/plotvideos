from typing import Optional, Tuple

from loguru import logger

from crud.video_crud import VideoCrud
from core.config import S7_UPLOAD_BATCH_SIZE
from core.enums import VideoStatus
from core.models import Video
from utils.media_utils import generate_hls


def transcode_video(video: Video) -> bool:
    """CPU-bound: generate HLS variants. Run one video at a time."""
    if not video.store_path.video.exists():
        VideoCrud.record_failure(
            video.id,
            VideoStatus.meta_translated.log(
                f"Video '{video.store_path.video}' does not exist"
            ),
        )
        logger.error(
            f"[{video.id} | {video.host}] Video '{video.store_path.video}' does not exist"
        )
        return False

    generate_hls(video.store_path.video, video.store_path.hls_dir)
    logger.info(f"[{video.id} | {video.host}] HLS variants generated")
    return True


def process_batch(last_id: Optional[int]) -> Tuple[bool, Optional[int]]:
    """Transcode one batch of meta-translated videos to HLS; set ``hls_ready``."""
    videos = VideoCrud.batch_get(last_id, S7_UPLOAD_BATCH_SIZE, VideoStatus.meta_translated)
    if not videos:
        return False, None

    exception_count = 0
    for video in videos:
        try:
            if transcode_video(video):
                VideoCrud.update(
                    {
                        "id": video.id,
                        "status": VideoStatus.hls_ready,
                        "failed_reason": "",
                    }
                )
        except Exception as e:
            VideoCrud.record_failure(video.id, VideoStatus.hls_ready.log(e))
            exception_count += 1
            logger.error(f"Error in transcode: {str(e)}")
            if exception_count >= 3:
                raise e

    return True, videos[-1].id


def generate_hls_videos():
    last_id = None

    while True:
        had_work, last_id = process_batch(last_id)
        if not had_work:
            break
