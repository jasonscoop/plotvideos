import time
import traceback

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.config import S4_SUBTITLE_BATCH_SIZE
from src.lib.models import VideoStatus
from src.utils.file_utils import rm_video

from src.lib.models import Video

from src.utils.whisper_utils import whisper_transcribe


def subtitle_video(video: Video):
    try:
        vtt_content, word_count = whisper_transcribe(video.store_path.audio)
        video.store_path.vtt.write_text(vtt_content)
        VideoCrud.update(
            {
                "id": video.id,
                "word_count": word_count,
                "subtitle_duration_ratio": round(word_count / video.duration, 2) if video.duration > 0 else 0,
                "status": VideoStatus.subtitled,
                "failed_reason": "",
            }
        )
        logger.info(
            f"[{video.id} | {video.host} | {video.original_id}] subtitle generated"
        )
        return None
    except Exception as e:
        reason = VideoCrud.update_status(
            video.id, VideoStatus.failed, VideoStatus.subtitled.log(e)
        )
        logger.info(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
        traceback.print_exc()
        rm_video(video)
        return e


def subtitle_videos(host: str = ""):
    last_id = 0

    while True:
        videos = VideoCrud.batch_get(
            last_id, S4_SUBTITLE_BATCH_SIZE, VideoStatus.converted, host
        )
        if not videos:
            logger.info("All subtitled, sleeping for 5 minutes")
            time.sleep(5 * 60)
            last_id = 0
            continue

        last_id = videos[-1].id
        for video in videos:
            subtitle_video(video)
