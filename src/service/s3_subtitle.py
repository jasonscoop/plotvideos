import traceback

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.config import MAX_ACCEPT_VIDEO_SIZE
from src.lib.models import VideoStatus
from src.utils.azure_subtitle_utils import generate_subtitle
from src.utils.log_utils import init_logging


def process_downloaded_videos(batch_size: int = 10):
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.downloaded)
        if not videos:
            break

        last_id = videos[-1].id

        for video in videos:
            if video.file_size > MAX_ACCEPT_VIDEO_SIZE:
                reason = f"[{video.id}] Video size exceeded: has size {video.file_size}  > {MAX_ACCEPT_VIDEO_SIZE}"
                VideoCrud.update_status(video.id, VideoStatus.skipped_due_to_size, reason)
                logger.info(reason)
                continue

            try:
                VideoCrud.update({
                    "id": video.id,
                    "subtitle_content": generate_subtitle(video),
                    "status": VideoStatus.subtitled
                })
                logger.info(f"Generated subtitle successfully for: {video.title}")
            except Exception as e:
                reason = str(e)[:1000]
                VideoCrud.update_status(video.id, VideoStatus.failed_subtitled, reason)
                logger.error(f"Failed to generate subtitle: {reason}")
                exception_count += 1
                if exception_count >= 3:
                    raise e
                traceback.print_exc()


if __name__ == '__main__':
    init_logging("subtitle")
    process_downloaded_videos()
