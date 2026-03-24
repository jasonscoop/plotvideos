import time
import traceback

from loguru import logger

from crawler.crud.video_crud import VideoCrud
from crawler.core.config import S4_SUBTITLE_BATCH_SIZE, SUBTITLE_TOKEN_RATIO_THRESHOLD
from crawler.core.models import VideoStatus
from crawler.utils.file_utils import rm_video

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
            logger.warning(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
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
                f"[{video.id} | {video.host} | {video.original_id}] low_density: {word_density} < {SUBTITLE_TOKEN_RATIO_THRESHOLD}"
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
            f"[{video.id} | {video.host} | {video.original_id}] subtitle generated"
        )
        return None
    except Exception as e:
        reason = VideoCrud.record_failure(
            video.id, VideoStatus.subtitled.log(e)
        )
        logger.info(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
        traceback.print_exc()
        return e


def subtitle_videos(host: str = ""):
    setup_graceful_shutdown()
    last_id = None

    while not should_stop():
        videos = VideoCrud.batch_get(
            last_id, S4_SUBTITLE_BATCH_SIZE, VideoStatus.converted, host
        )
        if not videos:
            logger.info("All subtitled, sleeping for 5 minutes")
            time.sleep(5 * 60)
            last_id = None
            continue

        last_id = videos[-1].id
        for video in videos:
            subtitle_video(video)
