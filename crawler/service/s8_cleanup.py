from loguru import logger

from crawler.crud.video_crud import VideoCrud
from crawler.core.enums import VideoStatus
from crawler.utils.file_utils import rm_video


def clean_files(batch_size, host):
    last_id = None
    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.uploaded, host)
        if not videos:
            break
        last_id = videos[-1].id
        for video in videos:
            rm_video(video)
            logger.info(f"[{video.id} | {video.host} | {video.original_id}] remove all files")

    # Clean up permanently failed videos
    last_id = None
    while True:
        videos = VideoCrud.get_exceeded_failed(last_id, batch_size, host)
        if not videos:
            break
        last_id = videos[-1].id
        for video in videos:
            rm_video(video)
            logger.info(f"[{video.id} | {video.host} | {video.original_id}] remove permanently failed files")
