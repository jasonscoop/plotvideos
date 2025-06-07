import sys
import traceback

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.config import MAX_ACCEPT_VIDEO_SIZE
from src.lib.consts import DB_ERROR_LOG_LENGTH
from src.lib.models import VideoStatus
from src.utils.azure_subtitle_utils import generate_subtitle
from src.utils.log_utils import init_logging
from src.utils.string_utils import get_tokens


def subtitle_videos(batch_size: int = 10, host: str = ""):
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.downloaded, host)
        if not videos:
            break

        last_id = videos[-1].id

        for video in videos:
            if video.file_size > MAX_ACCEPT_VIDEO_SIZE:
                reason = f"[{video.id} | {video.host} | {video.original_id}] size exceeded: {MAX_ACCEPT_VIDEO_SIZE}"
                VideoCrud.update_status(video.id, VideoStatus.skipped_due_to_size, reason)
                logger.info(reason)
                continue

            try:
                subtitle_content = generate_subtitle(video)
                tokens = get_tokens(subtitle_content)
                VideoCrud.update({
                    "id": video.id,
                    "subtitle_content": subtitle_content,
                    "subtitle_tokens": tokens,
                    "subtitle_duration_ratio": round(tokens / video.duration, 1),
                    "status": VideoStatus.subtitled
                })
                logger.info(
                    f"[{video.id} | {video.host} | {video.original_id}] subtitle generated")
            except Exception as e:
                reason = str(e)[:DB_ERROR_LOG_LENGTH]
                VideoCrud.update_status(video.id, VideoStatus.failed_subtitled, reason)
                exception_count += 1
                if exception_count >= 3:
                    raise e
                traceback.print_exc()


if __name__ == '__main__':
    init_logging("subtitle")
    host = sys.argv[1] if len(sys.argv) > 1 else ""
    subtitle_videos(10, host)
    logger.info("All subtitles generated")
