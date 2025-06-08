from pathlib import Path

import yt_dlp
from tenacity import stop_after_attempt, retry, wait_fixed

from src.lib.config import YT_DLP_PROXY, MAX_ACCEPT_VIDEO_SIZE


class SizeLimitExceeded(Exception):
    pass


def to_mb(byte_nums: int) -> float:
    return "{byte_nums / 1024 / 1024:.2f}"


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), reraise=True)
def download_remote_video(url: str, video_save_dir: Path) -> (str, dict):
    video_save_dir.mkdir(exist_ok=True, parents=True)
    output_template = str(video_save_dir.joinpath(f"%(id)s.%(ext)s"))

    def progress_hook(d):
        if d.get('total_bytes_estimate'):
            if d['total_bytes_estimate'] > MAX_ACCEPT_VIDEO_SIZE:
                raise SizeLimitExceeded(
                    f"Size [{d['total_bytes_estimate'] / 1024 / 1024:.2f} MB] exceed [{MAX_ACCEPT_VIDEO_SIZE}]")

    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'proxy': YT_DLP_PROXY,
        'progress_hooks': [progress_hook],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(ydl.prepare_filename(info)).name, info
