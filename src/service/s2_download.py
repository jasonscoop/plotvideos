import json
import traceback

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.consts import DB_ERROR_LOG_LENGTH
from src.lib.models import VideoStatus
from src.lib.schemas import StorePath
from src.utils.download_utils import download_remote_video
from src.utils.log_utils import init_logging


def download_videos(batch_size: int = 10):
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.fetched)
        if not videos:
            break

        last_id = videos[-1].id

        for video in videos:
            logger.info(f"[{video.id} | {video.host} | {video.original_id}] download started")
            path = StorePath(video.host, video.original_id)

            try:
                video_filename, info = download_remote_video(video.url, path.parent)
                path.parent.joinpath(f"info-{video.id}.json").write_text(json.dumps(info))
                VideoCrud.update({
                    "id": video.id,
                    "status": VideoStatus.downloaded,
                    "filename": video_filename,
                    "tags": info.get("tags", []),
                    "categories": info.get("categories", []),
                    "duration": info.get("duration", 0),
                    "file_size": path.parent.joinpath(video_filename).stat().st_size
                })
                logger.info(f"[{video.id} | {video.host} | {video.original_id}]  Downloaded")
            except Exception as e:
                reason = str(e).strip()[:DB_ERROR_LOG_LENGTH]
                VideoCrud.update_status(video.id, VideoStatus.failed_downloaded, reason)
                exception_count += 1
                if exception_count >= 3:
                    raise e
                traceback.print_exc()


if __name__ == "__main__":
    init_logging("download")
    download_videos()
    logger.info("All downloaded")
