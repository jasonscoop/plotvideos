import sys
import traceback

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.config import MAX_ACCEPT_VIDEO_SIZE, MIN_ACCEPT_DURATION
from src.lib.consts import AZURE_STT_MAX_DURATION, AZURE_STT_MAX_AUDIO_SIZE
from src.lib.enums import ErrorAt
from src.lib.models import VideoStatus
from src.lib.schemas import StorePath
from src.utils.azure_stt_utils import get_video_duration, media_to_wav
from src.utils.download_utils import to_mb
from src.utils.log_utils import init_logging


def convert_video(video):
    if video.file_size > MAX_ACCEPT_VIDEO_SIZE:
        reason = VideoCrud.update_status(video.id, VideoStatus.failed,
                                         ErrorAt.convert.out(f"Video large than {to_mb(MAX_ACCEPT_VIDEO_SIZE)}."))
        logger.warning(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
        return

    path = StorePath(video.host, video.original_id)
    video_path = path.parent / video.filename
    if not video_path.exists():
        reason = VideoCrud.update_status(video.id, VideoStatus.failed,
                                         ErrorAt.convert.out(f"Video file {video_path} not found."))
        logger.warning(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
        return

    duration = video.duration
    if duration == 0:
        duration = get_video_duration(video_path)

    if duration > AZURE_STT_MAX_DURATION:
        reason = VideoCrud.update_status(video.id, VideoStatus.failed,
                                         ErrorAt.convert.out(f"Duration is longer than {AZURE_STT_MAX_DURATION}"))
        logger.warning(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
        return

    if duration < MIN_ACCEPT_DURATION:
        reason = VideoCrud.update_status(video.id, VideoStatus.failed,
                                         ErrorAt.convert.out(f"Duration is shorter than {MIN_ACCEPT_DURATION}"))
        logger.warning(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
        return

    media_to_wav(video_path, path.audio)
    audio_size = path.audio.stat().st_size
    if audio_size > AZURE_STT_MAX_AUDIO_SIZE:
        reason = VideoCrud.update_status(video.id, VideoStatus.failed,
                                         ErrorAt.convert.out(f"Audio large then {to_mb(AZURE_STT_MAX_DURATION)}"))
        logger.warning(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
        return

    VideoCrud.update({
        "id": video.id,
        "duration": duration,
        "status": VideoStatus.converted,
        "failed_reason": "",
    })
    logger.info(f"[{video.id} | {video.host} | {video.original_id}] converted to audio")


def convert_videos(batch_size: int = 10, host: str = ""):
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.downloaded, host)
        if not videos:
            break

        last_id = videos[-1].id
        for video in videos:
            try:
                convert_video(video)
            except Exception as e:
                VideoCrud.update_status(video.id, VideoStatus.failed, ErrorAt.convert.out(str(e)))
                exception_count += 1
                if exception_count > 3:
                    raise
                else:
                    traceback.print_exc()


if __name__ == '__main__':
    init_logging("convert")

    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    host = sys.argv[2] if len(sys.argv) > 2 else ""

    convert_videos(batch_size, host)
    logger.info("All video converted.")
