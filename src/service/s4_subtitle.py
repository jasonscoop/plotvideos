import asyncio
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.models import VideoStatus
from src.utils.azure_subtitle_utils import generate_subtitle
from src.utils.file_utils import rm_video
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
            logger.info("All subtitled, sleeping for 5 minutes")
            time.sleep(5 * 60)
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
