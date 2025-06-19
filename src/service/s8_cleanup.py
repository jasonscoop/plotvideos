from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.enums import VideoStatus
from src.utils.file_utils import rm_video


def clean_files(batch_size, host):
    last_id = 0
    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, [VideoStatus.failed, VideoStatus.uploaded], host)
        if not videos:
            break

        last_id = videos[-1].id
        for video in videos:
            rm_video(video)
            logger.info(f"[{video.id} | {video.host} | {video.original_id}] remove all files")
