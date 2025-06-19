import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from loguru import logger

from src.crud.language_crud import LanguageCrud
from src.crud.video_crud import VideoCrud
from src.lib.config import BUNNY_API_KEY, BUNNY_LIBRARY_ID, BUNNY_CDN_DOMAIN
from src.lib.enums import VideoStatus
from src.lib.models import Video, Language
from src.utils.bunny_utils import BunnyStreamClient
from src.utils.file_utils import upload_dir_to_s3, rm_video

bunny_client = BunnyStreamClient(BUNNY_API_KEY, BUNNY_LIBRARY_ID)


def upload_video(video: Video, languages: List[Language]):
    if not video.path.video.exists():
        VideoCrud.update_status(video.id, VideoStatus.failed,
                                VideoStatus.uploaded.log("Video '{video.path.video}' does not exist"))
        rm_video(video)
        logger.error(f"[{video.id} | {video.host} | {video.original_id}]  Video '{video.path.video}' does not exist")
        return

    try:
        logger.info(f"[{video.id} | {video.host} | {video.original_id}] start uploading")
        guid = bunny_client.upload_video(video)
        logger.info(f"[{video.id} | {video.host} | {video.original_id}] uploaded video as {guid}")

        for lang in languages:
            vtt_file = video.path.translated_vtts / f"{lang.code}.vtt"
            if not vtt_file.exists():
                logger.warning(
                    f"[{video.id} | {video.host} | {video.original_id}] vtt file '{lang.code}' not found, skipped")
                continue
            bunny_client.upload_subtitle(guid, vtt_file, lang)
            logger.info(f"[{video.id} | {video.host} | {video.original_id}] uploaded '{lang.code}'")

        VideoCrud.update({
            "id": video.id,
            "bunny_video_id": guid,
            "bunny_library_id": BUNNY_LIBRARY_ID,
            "bunny_cdn_domain": BUNNY_CDN_DOMAIN,
            "status": VideoStatus.uploaded,
            "failed_reason": "",
        })
        upload_dir_to_s3(video.path.parent, video.path.prefix)
        logger.info(f"[{video.id} | {video.host} | {video.original_id}] uploaded video and vtts")
    except Exception as e:
        VideoCrud.update_status(video.id, VideoStatus.failed, VideoStatus.uploaded.log(e))
        raise e
    finally:
        rm_video(video)


def upload_videos(batch_size: int = 10, host: str = ""):
    last_id = 0
    exception_count = 0
    languages = LanguageCrud.get_all()

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.meta_translated, host)
        if not videos:
            logger.info("All uploaded, sleeping for 5 minutes")
            time.sleep(5 * 60)
            last_id = 0
            languages = LanguageCrud.get_all()
            continue

        last_id = videos[-1].id

        with ThreadPoolExecutor(max_workers=len(videos)) as executor:
            futures = [executor.submit(upload_video, video, languages) for video in videos]
            for future in as_completed(futures):
                try:
                    future.result()  # This will raise any exceptions that occurred
                except Exception as e:
                    exception_count += 1
                    logger.error(f"Error in upload: {str(e)}")
                    if exception_count >= 3:
                        raise e
