import asyncio
import sys
import traceback

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.config import BUNNY_API_KEY, BUNNY_LIBRARY_ID
from src.lib.consts import DB_ERROR_LOG_LENGTH
from src.lib.enums import VideoStatus, Language
from src.lib.schemas import StorePath
from src.utils.bunny_utils import BunnyStreamClient
from src.utils.file_utils import upload_dir_to_s3
from src.utils.log_utils import init_logging


def upload_videos(batch_size: int = 10, host: str = ""):
    bunny_client = BunnyStreamClient(BUNNY_API_KEY, BUNNY_LIBRARY_ID)
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.meta_translated, host)
        if not videos:
            break

        last_id = videos[-1].id
        for video in videos:
            path = StorePath(video.host, video.original_id)

            try:
                guid = bunny_client.upload_video(video, path)
                for lang in Language:
                    vtt_file = path.translated_vtts / f"{lang.short_code}.vtt"
                    if not vtt_file.exists():
                        logger.warning(f"[{video.id} | {video.host} | {video.original_id}] vtt file not found, skipped")
                        continue
                    bunny_client.upload_subtitle(guid, vtt_file, lang)

                VideoCrud.update({
                    "id": video.id,
                    "bunny_video_id": guid,
                    "status": VideoStatus.uploaded
                })
                asyncio.run(upload_dir_to_s3(path.parent, path.prefix))
                logger.info(f"[{video.id} | {video.host} | {video.original_id}] uploaded")
            except Exception as e:
                reason = str(e)[:DB_ERROR_LOG_LENGTH]
                VideoCrud.update_status(video.id, VideoStatus.failed_uploaded, reason)
                exception_count += 1
                if exception_count >= 3:
                    raise e
                traceback.print_exc()


if __name__ == '__main__':
    init_logging("upload")
    host = sys.argv[1] if len(sys.argv) > 1 else ""
    upload_videos(10, host)
    logger.info("All uploaded")
