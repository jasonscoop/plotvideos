import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from loguru import logger

from crawler.crud.video_crud import VideoCrud
from crawler.core.config import S7_UPLOAD_BATCH_SIZE
from crawler.core.enums import VideoStatus
from crawler.core.languages import Language
from crawler.core.models import Video
from crawler.utils.b2_utils import get_b2_client
from crawler.utils.file_utils import rm_video
from crawler.utils.media_utils import generate_hls


def transcode_video(video: Video):
    """CPU-bound: generate HLS variants. Run sequentially, one at a time."""
    if not video.store_path.video.exists():
        VideoCrud.record_failure(
            video.id,
            VideoStatus.uploaded.log(
                f"Video '{video.store_path.video}' does not exist"
            ),
        )
        logger.error(
            f"[{video.id} | {video.host} | {video.original_id}] Video '{video.store_path.video}' does not exist"
        )
        return False

    logger.info(
        f"[{video.id} | {video.host} | {video.original_id}] generating HLS variants"
    )
    generate_hls(video.store_path.video, video.store_path.hls_dir)
    logger.info(
        f"[{video.id} | {video.host} | {video.original_id}] HLS variants generated"
    )
    return True


def upload_video(video: Video, languages: List[Language]):
    """I/O-bound: upload to B2, then clean local files."""
    try:
        logger.info(
            f"[{video.id} | {video.host} | {video.original_id}] start uploading to B2"
        )

        b2_client = get_b2_client()
        upload_results = b2_client.upload_video_and_subtitles(video, languages)

        logger.info(
            f"[{video.id} | {video.host} | {video.original_id}] uploaded video and {len(upload_results['subtitle_urls'])} subtitle files to B2"
        )

        rm_video(video)
        logger.info(
            f"[{video.id} | {video.host} | {video.original_id}] cleaned up local files"
        )

        VideoCrud.update(
            {
                "id": video.id,
                "status": VideoStatus.uploaded,
                "failed_reason": "",
            }
        )
    except Exception as e:
        VideoCrud.record_failure(video.id, VideoStatus.uploaded.log(e))
        raise e


def upload_videos(host: str = ""):
    last_id = None
    exception_count = 0
    languages = Language.get_all()

    while True:
        videos = VideoCrud.batch_get(
            last_id, S7_UPLOAD_BATCH_SIZE, VideoStatus.meta_translated, host
        )
        if not videos:
            logger.info("All uploaded, sleeping for 5 minutes")
            time.sleep(5 * 60)
            last_id = None
            continue

        last_id = videos[-1].id

        # Transcode sequentially (CPU-bound — one ffmpeg at a time)
        ready = []
        for video in videos:
            try:
                if transcode_video(video):
                    ready.append(video)
            except Exception as e:
                VideoCrud.record_failure(video.id, VideoStatus.uploaded.log(e))
                exception_count += 1
                logger.error(f"Error in transcode: {str(e)}")
                if exception_count >= 3:
                    raise e

        # Upload in parallel (I/O-bound)
        if ready:
            with ThreadPoolExecutor(max_workers=len(ready)) as executor:
                futures = [
                    executor.submit(upload_video, video, languages) for video in ready
                ]
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Exception as e:
                        exception_count += 1
                        logger.error(f"Error in upload: {str(e)}")
                        if exception_count >= 3:
                            raise e
