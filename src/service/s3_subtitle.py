import sys
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.config import MAX_ACCEPT_VIDEO_SIZE
from src.lib.consts import DB_ERROR_LOG_LENGTH
from src.lib.models import VideoStatus
from src.utils.azure_subtitle_utils import generate_subtitle
from src.utils.download_utils import to_mb
from src.utils.log_utils import init_logging
from src.utils.string_utils import get_tokens


def subtitle_video(video):
    if video.file_size > MAX_ACCEPT_VIDEO_SIZE:
        reason = f"[{video.id} | {video.host} | {video.original_id}] size exceeded: {to_mb(MAX_ACCEPT_VIDEO_SIZE)}"
        VideoCrud.update_status(video.id, VideoStatus.skipped_due_to_size, reason)
        logger.error(reason)
        return None

    try:
        subtitle_content, duration = generate_subtitle(video)
        if duration == 0:
            reason = f"[{video.id} | {video.host} | {video.original_id}] duration is 0."
            VideoCrud.update_status(video.id, VideoStatus.skipped_due_to_zero_duration, reason)
            logger.error(reason)
            return None

        tokens = get_tokens(subtitle_content)
        VideoCrud.update({
            "id": video.id,
            "subtitle_content": subtitle_content,
            "subtitle_tokens": tokens,
            "duration": duration,
            "subtitle_duration_ratio": round(tokens / video.duration, 2),
            "status": VideoStatus.subtitled,
            "failed_reason": "",
        })
        logger.info(f"[{video.id} | {video.host} | {video.original_id}] subtitle generated")
        return None
    except Exception as e:
        reason = str(e)[:DB_ERROR_LOG_LENGTH]
        VideoCrud.update_status(video.id, VideoStatus.failed_subtitled, reason)
        traceback.print_exc()
        return e


def subtitle_videos(batch_size: int = 10, host: str = ""):
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.downloaded, host)
        if not videos:
            break

        last_id = videos[-1].id

        with ThreadPoolExecutor(max_workers=len(videos)) as executor:
            futures = [executor.submit(subtitle_video, video) for video in videos]
            for future in as_completed(futures):
                error = future.result()
                if error:
                    exception_count += 1
                    if exception_count >= 3:
                        raise error


if __name__ == '__main__':
    init_logging("subtitle")

    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    host = sys.argv[2] if len(sys.argv) > 2 else ""

    subtitle_videos(batch_size, host)
    logger.info("All subtitles generated")
