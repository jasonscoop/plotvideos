import logging
import os
import yt_dlp

from src.lib.config import VIDEOS_DIR
from src.lib.connection import SessionLocal
from src.lib.log_utils import init_logging
from src.lib.models import Video, VideoStatus


def download_video(video: Video) -> (bool, str, str):
    video_dir = VIDEOS_DIR.joinpath(video.host, video.original_id)
    if video_dir.exists():
        logging.warning("Video dir [%s] exists, ignore", video_dir)
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
    }
    file_path = ""
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([video.url])
            # Find the newest file in the directory as the downloaded file
            files = sorted(
                [video_dir / filename for filename in os.listdir(video_dir)],
                key=lambda f: f.stat().st_mtime,
                reverse=True
            )
            file_path = str(os.path.basename(files[0])) if files else ""
        return True, file_path, ""
    except Exception as e:
        logging.error(f"Failed to download {video.url}: {e}")
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

            logging.info(f"Processing batch of {len(videos)} videos (last_id {last_id})")
            for video in videos:
                logging.info(f"Downloading: {video.title} ({video.url})")
                success, file_path, error = download_video(video)
                if success:
                    video.status = VideoStatus.downloaded
                    video.path = file_path
                    video.failed_reason = ""
                    logging.info(f"Downloaded successfully: {file_path}")
                else:
                    video.status = VideoStatus.download_failed
                    video.failed_reason = error[:1000]  # Truncate if too long
                    logging.error(f"Download failed: {error}")
                session.commit()
            last_id = videos[-1].id
    finally:
        session.close()


if __name__ == "__main__":
    init_logging("download-videos")
    result = download_video(Video(url="https://www.youtube.com/watch?v=UkRaqAuIIOU", original_id="UkRaqAuIIOU", host="www.youtube.com"))
    logging.info(result)
