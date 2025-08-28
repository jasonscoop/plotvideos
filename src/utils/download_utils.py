from pathlib import Path

import yt_dlp
from tenacity import stop_after_attempt, retry, wait_fixed

from src.lib.config import YT_DLP_PROXY, MAX_ACCEPT_VIDEO_SIZE


class SizeLimitExceeded(Exception):
    pass


def to_mb(byte_size: int) -> float:
    return round(int(byte_size) / 1024 / 1024)


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), reraise=True)
def download_remote_video(url: str, video_path: Path) -> dict:
    video_path.parent.mkdir(exist_ok=True, parents=True)

    def progress_hook(d):
        if d.get("total_bytes_estimate"):
            if d["total_bytes_estimate"] > MAX_ACCEPT_VIDEO_SIZE:
                raise SizeLimitExceeded(
                    f"Size [{to_mb(d['total_bytes_estimate'])} MB] exceeded [{to_mb(MAX_ACCEPT_VIDEO_SIZE)} MB]"
                )

    ydl_opts = {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "outtmpl": str(video_path),
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "writesubtitles": False,
        "writeautomaticsub": False,
        "proxy": YT_DLP_PROXY,
        "progress_hooks": [progress_hook],
        "merge_output_format": "mp4",
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(url, download=True)
