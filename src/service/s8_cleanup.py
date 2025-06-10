import shutil
import sys

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.enums import VideoStatus
from src.lib.schemas import StorePath
from src.utils.log_utils import init_logging


def clean_files(batch_size, host):
    last_id = 0
    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, [VideoStatus.failed, VideoStatus.uploaded], host)
        if not videos:
            break

        last_id = videos[-1].id
        for video in videos:
            path: StorePath = StorePath(video.host, video.original_id)
            shutil.rmtree(str(path.parent), ignore_errors=True)


if __name__ == '__main__':
    init_logging("cleanup")
    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    host = sys.argv[2] if len(sys.argv) > 2 else ""
    clean_files(batch_size, host)
    logger.info("All failed cleaned")
