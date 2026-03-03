import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from loguru import logger

from crawler.crud.language_crud import LanguageCrud
from crawler.crud.video_crud import VideoCrud
from crawler.lib.config import S7_UPLOAD_BATCH_SIZE
from crawler.lib.enums import VideoStatus
from crawler.lib.models import Video, Language
from crawler.utils.b2_utils import get_b2_client
from crawler.utils.file_utils import rm_video
from crawler.utils.media_utils import generate_hls


def upload_video(video: Video, languages: List[Language]):
    if not video.store_path.video.exists():
        VideoCrud.update_status(
            video.id,
            VideoStatus.failed,
            VideoStatus.uploaded.log(
                f"Video '{video.store_path.video}' does not exist"
            ),
        )
        logger.error(
            f"[{video.id} | {video.host} | {video.original_id}] Video '{video.store_path.video}' does not exist"
        )
        return

    try:
        logger.info(
            f"[{video.id} | {video.host} | {video.original_id}] generating HLS variants"
        )
        generate_hls(video.store_path.video, video.store_path.hls_dir)
        logger.info(
            f"[{video.id} | {video.host} | {video.original_id}] HLS variants generated"
        )

        logger.info(
            f"[{video.id} | {video.host} | {video.original_id}] start uploading to B2"
        )

        b2_client = get_b2_client()
        upload_results = b2_client.upload_video_and_subtitles(video, languages)

        logger.info(
            f"[{video.id} | {video.host} | {video.original_id}] uploaded to B2: {upload_results['video_url']}"
        )

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


def cleanup_files(host: str = ""):
    last_id = None
    total_cleaned = 0
    while True:
        videos = VideoCrud.batch_get(
            last_id, S7_UPLOAD_BATCH_SIZE, [VideoStatus.failed, VideoStatus.published], host
        )
        if not videos:
            break

        last_id = videos[-1].id
        for video in videos:
            rm_video(video)
            total_cleaned += 1
            logger.info(f"[{video.id} | {video.host} | {video.original_id}] cleaned up files")

    if total_cleaned > 0:
        logger.info(f"Cleanup completed: {total_cleaned} videos cleaned")


def upload_videos(host: str = ""):
    last_id = None
    exception_count = 0
    languages = LanguageCrud.get_all()

    while True:
        videos = VideoCrud.batch_get(
            last_id, S7_UPLOAD_BATCH_SIZE, VideoStatus.meta_translated, host
        )
        if not videos:
            cleanup_files(host)
            logger.info("All uploaded, sleeping for 5 minutes")
            time.sleep(5 * 60)
            last_id = None
            languages = LanguageCrud.get_all()
            continue

        last_id = videos[-1].id

        with ThreadPoolExecutor(max_workers=len(videos)) as executor:
            futures = [
                executor.submit(upload_video, video, languages) for video in videos
            ]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    exception_count += 1
                    logger.error(f"Error in upload: {str(e)}")
                    if exception_count >= 3:
                        raise e
