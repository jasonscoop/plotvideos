from loguru import logger
import os
import yt_dlp

from src.lib.config import VIDEOS_DIR, YT_DLP_PROXY
from src.lib.connection import SessionLocal
from src.lib.consts import SUPPORTED_VIDEO_EXTENSIONS
from src.utils.log_utils import init_logging
from src.lib.models import Video, VideoStatus


def download_video(video: Video) -> (bool, str, str):
    video_uri_base = f"{video.host}/{video.original_id[0:2]}/{video.original_id}"
    video_dir = VIDEOS_DIR / video_uri_base
    filenames ={f"{video.original_id}.{ext}" for ext in SUPPORTED_VIDEO_EXTENSIONS}

    if any(video_dir.joinpath(filename).exists() for filename in filenames):
        logger.warning("Video dir [%s] exists, ignore", video_dir)
        return False, "", f"Video dir exists: [{video_dir}]"

    video_dir.mkdir(exist_ok=True, parents=True)
    output_template = str(video_dir.joinpath(f"%(id)s.%(ext)s"))
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'merge_output_format': 'mp4',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'proxy': YT_DLP_PROXY
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video.url])
            for filename in filenames:
                if video_dir.joinpath(filename).exists():
                    return True, f"{video_uri_base}/{filename}", ""
        return False, "", "Can't find downloaded video file."
    except Exception as e:
        logger.error(f"Failed to download {video.url}: {e}")
        return False, "", str(e)


def download_videos():
    session = SessionLocal()
    batch_size = 10  # You can adjust this as needed
    last_id = 0
    try:
        while True:
            videos = (
                session.query(Video)
                .filter(Video.status == VideoStatus.added, Video.id > last_id)
                .order_by(Video.id)
                .limit(batch_size)
                .all()
            )
            if not videos:
                break

            logger.info(f"Processing batch of {len(videos)} videos (last_id {last_id})")
            for video in videos:
                logger.info(f"Downloading: {video.title} ({video.url})")
                success, file_path, error = download_video(video)
                if success:
                    video.status = VideoStatus.downloaded
                    video.path = file_path
                    video.failed_reason = ""
                    logger.info(f"Downloaded successfully: {file_path}")
                else:
                    video.status = VideoStatus.download_failed
                    video.failed_reason = error[:1000]  # Truncate if too long
                    logger.error(f"Download failed: {error}")
                session.commit()
            last_id = videos[-1].id
    finally:
        session.close()


if __name__ == "__main__":
    init_logging("download-videos")
    # download_videos()
    r = download_video(Video(url="https://www.pornhub.com/view_video.php?viewkey=661bb3bde2251", original_id="661bb3bde2251", host="www.pornhub.com"))
    logger.info(r)
    logger.info("All done!")
