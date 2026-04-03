from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Tuple

from loguru import logger

from crud.video_crud import VideoCrud
from core.config import S7_UPLOAD_BATCH_SIZE
from core.enums import VideoStatus
from core.languages import Language
from core.models import Video
from utils.b2_utils import get_b2_client
from utils.file_utils import rm_video


def upload_video(video: Video, languages: List[Language]) -> None:
    """Upload to B2, then remove local copy."""
    try:
        logger.info(f"[{video.id} | {video.host}] start uploading to B2")

        b2_client = get_b2_client()
        upload_results = b2_client.upload_video_and_subtitles(video, languages)

        logger.info(
            f"[{video.id} | {video.host}] uploaded video and "
            f"{len(upload_results['subtitle_urls'])} subtitle files to B2"
        )

        VideoCrud.update(
            {
                "id": video.id,
                "status": VideoStatus.uploaded.value,
                "failed_reason": "",
            }
        )
        try:
            rm_video(video)
        except OSError as e:
            logger.warning(f"[{video.id} | {video.host}] rm_video after upload: {e}")
    except Exception as e:
        VideoCrud.record_failure(video.id, VideoStatus.uploaded.log(e))
        raise e


def process_batch(last_id: Optional[int]) -> Tuple[bool, Optional[int]]:
    """Upload one batch of ``hls_ready`` videos to B2."""
    languages = Language.get_all()
    videos = VideoCrud.batch_get(last_id, S7_UPLOAD_BATCH_SIZE, VideoStatus.hls_ready)
    if not videos:
        return False, None

    exception_count = 0

    with ThreadPoolExecutor(max_workers=len(videos)) as executor:
        futures = [executor.submit(upload_video, video, languages) for video in videos]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                exception_count += 1
                logger.error(f"Error in upload: {str(e)}")
                if exception_count >= 3:
                    raise e

    return True, videos[-1].id


def upload_videos():
    last_id = None

    while True:
        had_work, last_id = process_batch(last_id)
        if not had_work:
            break
