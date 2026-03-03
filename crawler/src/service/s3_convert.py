import time
import traceback

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.config import MIN_ACCEPT_DURATION, S3_CONVERT_BATCH_SIZE
from src.lib.models import VideoStatus
from src.utils.file_utils import rm_video
from src.utils.media_utils import get_video_duration, media_to_wav


def convert_video(video):
    video_path = video.store_path.video
    if not video_path.exists():
        reason = VideoCrud.update_status(
            video.id,
            VideoStatus.failed,
            VideoStatus.converted.log(f"Video file {video_path} not found."),
        )
        logger.warning(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
        return

    duration = video.duration
    if duration == 0:
        duration = get_video_duration(video_path)

    if duration < MIN_ACCEPT_DURATION:
        reason = VideoCrud.update_status(
            video.id,
            VideoStatus.failed,
            VideoStatus.converted.log(
                f"Duration is shorter than {MIN_ACCEPT_DURATION}s"
            ),
        )
        logger.warning(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
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
    logger.info(f"[{video.id} | {video.host} | {video.original_id}] converted to audio")


def convert_videos(host: str = ""):
    last_id = None
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(
            last_id, S3_CONVERT_BATCH_SIZE, VideoStatus.downloaded, host
        )
        if not videos:
            logger.info("All converted, sleeping for 10 minutes")
            time.sleep(10 * 60)
            last_id = None
            continue

        last_id = videos[-1].id
        for video in videos:
            try:
                convert_video(video)
            except Exception as e:
                VideoCrud.update_status(
                    video.id, VideoStatus.failed, VideoStatus.converted.log(str(e))
                )
                exception_count += 1
                traceback.print_exc()
                if exception_count > 3:
                    raise
