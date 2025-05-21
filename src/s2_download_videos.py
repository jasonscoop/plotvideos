import logging
import os
import uuid

from src.lib.config import DOWNLOADS_DIR
from src.lib.connection import SessionLocal
from src.lib.models import Video, VideoStatus

# Add yt-dlp import
import yt_dlp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# No need to create DOWNLOADS_DIR here, assume it's handled in config or elsewhere

def download_video(video: Video) -> (bool, str, str):
    """
    Download video using yt-dlp Python SDK. Returns (success, file_path, error_message)
    """
    video_dir = DOWNLOADS_DIR / video.host
    video_dir.mkdir(exist_ok=True)
    output_template = str(video_dir.joinpath(f"%(id)s-%(title)s.%(ext)s"))
    ydl_opts = {
        'format': 'best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'writesubtitles': True,
        'writeautomaticsub': True,
        'allsubtitles': True,
        "subtitleslangs": ["all"],
    }
    file_path = ""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([video.url])
            # Find the newest file in the directory as the downloaded file
            files = sorted(
                [DOWNLOADS_DIR / f for f in os.listdir(DOWNLOADS_DIR)],
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            file_path = str(files[0]) if files else ""
        return True, file_path, ""
    except Exception as e:
        logger.error(f"Failed to download {video.url}: {e}")
        return False, "", str(e)


def main():
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
    download_video(Video(url="https://www.youtube.com/watch?v=UkRaqAuIIOU"))
