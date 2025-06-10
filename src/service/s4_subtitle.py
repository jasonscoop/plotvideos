import asyncio
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.models import VideoStatus
from src.utils.azure_subtitle_utils import generate_subtitle
from src.utils.file_utils import rm_video
from src.utils.log_utils import init_logging
from src.utils.string_utils import get_tokens


def subtitle_video(video):
    try:
        subtitle_content = generate_subtitle(video)
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
        asyncio.run(rm_video(video))
        return e


def subtitle_videos(batch_size: int = 10, host: str = ""):
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.converted, host)
        if not videos:
            time.sleep(5 * 60)
            logger.info("Sleeping for 5 minutes")
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


if __name__ == '__main__':
    init_logging("subtitle")

    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    host = sys.argv[2] if len(sys.argv) > 2 else ""

    subtitle_videos(batch_size, host)
    logger.info("All subtitles generated")
