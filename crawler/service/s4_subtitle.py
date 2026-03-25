import time
import traceback
from typing import Optional, Tuple

from loguru import logger

from crawler.crud.video_crud import VideoCrud
from crawler.core.config import S4_SUBTITLE_BATCH_SIZE, SUBTITLE_TOKEN_RATIO_THRESHOLD
from crawler.core.models import VideoStatus
from crawler.core.models import Video

from crawler.utils.signal_utils import setup_graceful_shutdown, should_stop
from crawler.utils.whisper_utils import whisper_transcribe


def subtitle_video(video: Video):
    try:
        if not video.store_path.audio.exists():
            reason = VideoCrud.record_failure(
                video.id,
                VideoStatus.subtitled.log(f"Audio file not found: {video.store_path.audio}"),
            )
            logger.warning(f"[{video.id} | {video.host}] {reason}")
            return None

        vtt_content, word_count = whisper_transcribe(video.store_path.audio)
        word_density = round(word_count / video.duration, 2) if video.duration > 0 else 0

        if word_density < SUBTITLE_TOKEN_RATIO_THRESHOLD:
            VideoCrud.update(
                {
                    "id": video.id,
                    "word_count": word_count,
                    "word_density": word_density,
                    "status": VideoStatus.low_density,
                    "failed_reason": f"Word density {word_density} below threshold {SUBTITLE_TOKEN_RATIO_THRESHOLD}",
                }
            )
            logger.warning(
                f"[{video.id} | {video.host}] low_density: {word_density} < {SUBTITLE_TOKEN_RATIO_THRESHOLD}"
            )
            return None

        video.store_path.vtt.write_text(vtt_content)
        VideoCrud.update(
            {
                "id": video.id,
                "word_count": word_count,
                "word_density": word_density,
                "status": VideoStatus.subtitled,
                "failed_reason": "",
            }
        )
        logger.info(
            f"[{video.id} | {video.host}] subtitle generated"
        )
        return None
    except Exception as e:
        reason = VideoCrud.record_failure(
            video.id, VideoStatus.subtitled.log(e)
        )
        logger.info(f"[{video.id} | {video.host}] {reason}")
        traceback.print_exc()
        return e


def process_batch(last_id: Optional[int]) -> Tuple[bool, Optional[int]]:
    """Subtitle one batch of converted videos. Returns (had_work, next_last_id)."""
    videos = VideoCrud.batch_get(last_id, S4_SUBTITLE_BATCH_SIZE, VideoStatus.converted)
    if not videos:
        return False, None

    for video in videos:
        subtitle_video(video)

    return True, videos[-1].id


def subtitle_videos():
    setup_graceful_shutdown()
    last_id = None

    while not should_stop():
        had_work, last_id = process_batch(last_id)
        if not had_work:
            logger.info("All subtitled, sleeping for 5 minutes")
            time.sleep(5 * 60)
            last_id = None
