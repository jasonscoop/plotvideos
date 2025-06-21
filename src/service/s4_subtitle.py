import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.config import S4_SUBTITLE_BATCH_SIZE
from src.lib.models import VideoStatus
from src.utils.file_utils import rm_video
from src.utils.string_utils import get_tokens
from src.utils.whisper_utils import whisper_transcribe


def subtitle_video(video):
    try:
        vtt_content, subtitle_content = whisper_transcribe(video.path)
        video.path.vtt.write_text(vtt_content)
        tokens = get_tokens(subtitle_content)
        VideoCrud.update({
            "id": video.id,
            "subtitle_content": subtitle_content,
            "subtitle_tokens": tokens,
            "subtitle_duration_ratio": round(tokens / video.duration, 2),
            "status": VideoStatus.subtitled,
            "failed_reason": "",
        })
        logger.info(f"[{video.id} | {video.host} | {video.original_id}] subtitle generated")
        return None
    except Exception as e:
        reason = VideoCrud.update_status(video.id, VideoStatus.failed, VideoStatus.subtitled.log(e))
        logger.info(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
        traceback.print_exc()
        rm_video(video)
        return e


def subtitle_videos(host: str = ""):
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, S4_SUBTITLE_BATCH_SIZE, VideoStatus.converted, host)
        if not videos:
            logger.info("All subtitled, sleeping for 5 minutes")
            time.sleep(5 * 60)
            last_id = 0
            continue

        last_id = videos[-1].id
        with ThreadPoolExecutor(max_workers=len(videos)) as executor:
            futures = [executor.submit(subtitle_video, video) for video in videos]
            for future in as_completed(futures):
                error = future.result()
                if error:
                    exception_count += 1
                    if exception_count >= 3:
                        raise error
