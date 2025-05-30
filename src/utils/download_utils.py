from pathlib import Path

import yt_dlp
from tenacity import stop_after_attempt, retry, wait_fixed

from src.lib.config import YT_DLP_PROXY


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), reraise=True)
def download_remote_video(url: str, video_save_dir: Path):
    video_save_dir.mkdir(exist_ok=True, parents=True)
    output_template = str(video_save_dir.joinpath(f"%(id)s.%(ext)s"))
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'writesubtitles': False,
        'writeautomaticsub': False,
        'proxy': YT_DLP_PROXY
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return Path(ydl.prepare_filename(info)).name
