import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from loguru import logger

from src.crud.language_crud import LanguageCrud
from src.crud.video_crud import VideoCrud
from src.lib.config import (
    S7_UPLOAD_BATCH_SIZE,
    B2_CDN_DOMAIN,
)
from src.lib.enums import VideoStatus
from src.lib.models import Video, Language
from src.utils.b2_utils import get_b2_client
from src.utils.file_utils import rm_video


def upload_video(video: Video, languages: List[Language]):
    if not video.store_path.video.exists():
        VideoCrud.update_status(
            video.id,
            VideoStatus.failed,
            VideoStatus.uploaded.log(
                f"Video '{video.store_path.video}' does not exist"
            ),
        )
        rm_video(video)
        logger.error(
            f"[{video.id} | {video.host} | {video.original_id}] Video '{video.store_path.video}' does not exist"
        )
        return

    try:
        logger.info(
            f"[{video.id} | {video.host} | {video.original_id}] start uploading to B2"
        )

        # Get B2 client and upload video and subtitles
        b2_client = get_b2_client()
        upload_results = b2_client.upload_video_and_subtitles(video, languages)

        logger.info(
            f"[{video.id} | {video.host} | {video.original_id}] uploaded to B2: {upload_results['video_url']}"
        )

        # Update database with B2 URLs
        VideoCrud.update(
            {
                "id": video.id,
                "status": VideoStatus.published,
                "failed_reason": "",
            }
        )

        logger.info(
            f"[{video.id} | {video.host} | {video.original_id}] uploaded video and {len(upload_results['subtitle_urls'])} subtitle files to B2"
        )
    except Exception as e:
        VideoCrud.update_status(
            video.id, VideoStatus.failed, VideoStatus.uploaded.log(e)
        )
        raise e
    finally:
        pass
    rm_video(video)


def upload_videos(host: str = ""):
    last_id = 0
    exception_count = 0
    languages = LanguageCrud.get_all()

    while True:
        videos = VideoCrud.batch_get(
            last_id, S7_UPLOAD_BATCH_SIZE, VideoStatus.meta_translated, host
        )
        if not videos:
            logger.info("All uploaded, sleeping for 5 minutes")
            time.sleep(5 * 60)
            last_id = 0
            languages = LanguageCrud.get_all()
            continue

        last_id = videos[-1].id

        with ThreadPoolExecutor(max_workers=len(videos)) as executor:
            futures = [
                executor.submit(upload_video, video, languages) for video in videos
            ]
            for future in as_completed(futures):
                try:
                    future.result()  # This will raise any exceptions that occurred
                except Exception as e:
                    exception_count += 1
                    logger.error(f"Error in upload: {str(e)}")
                    if exception_count >= 3:
                        raise e
