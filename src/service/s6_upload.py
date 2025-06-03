import traceback

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.config import BUNNY_API_KEY, BUNNY_LIBRARY_ID
from src.lib.consts import DB_ERROR_LOG_LENGTH
from src.lib.enums import VideoStatus, Language
from src.lib.schemas import StorePath
from src.utils.bunny_utils import BunnyStreamClient
from src.utils.log_utils import init_logging


def upload_videos(batch_size: int = 10):
    bunny_client = BunnyStreamClient(BUNNY_API_KEY, BUNNY_LIBRARY_ID)
    last_id = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.vtt_translated)
        if not videos:
            break

        logger.info(f"Processing batch of {len(videos)} videos (last_id {last_id})")
        last_id = videos[-1].id
        for video in videos:
            logger.info(f"[{video.id}] Uploading video and subtitles for: {video.title}")
            path = StorePath(video.host, video.original_id)

            try:
                guid = bunny_client.upload_video(video, path)
                for lang in Language:
                    vtt_file = path.translated_vtts / f"{lang.short_code}.vtt"
                    if not vtt_file.exists():
                        logger.warning(f"[{video.id}] subtitle file not found: {vtt_file}")
                        continue
                    bunny_client.upload_subtitle(guid, vtt_file, lang)

                VideoCrud.update({
                    "bunny_video_id": guid,
                    "status": VideoStatus.uploaded
                })
                logger.info(f"[{video.id}] Successfully uploaded video and subtitles: {video.title}")
            except Exception as e:
                reason = str(e)[:DB_ERROR_LOG_LENGTH]
                VideoCrud.update_status(video.id, VideoStatus.failed_uploaded, reason)
                traceback.print_exc()


if __name__ == '__main__':
    init_logging("upload")
    upload_videos()
