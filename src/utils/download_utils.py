from pathlib import Path
import random
import time
from typing import Optional
from loguru import logger
import yt_dlp
import requests
from tenacity import stop_after_attempt, retry, wait_fixed, wait_exponential

from src.lib.config import YT_DLP_PROXY, MAX_ACCEPT_VIDEO_SIZE
from src.lib.consts import USER_AGENTS


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


@retry(
    wait=wait_exponential(multiplier=1, min=1, max=10),
    stop=stop_after_attempt(3),
    reraise=True,
)
def download_image(url: str, image_path: Path) -> bool:
    image_path.parent.mkdir(exist_ok=True, parents=True)

    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "image/webp,image/apng,image/*,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "image",
        "Sec-Fetch-Mode": "no-cors",
        "Sec-Fetch-Site": "cross-site",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
    }

    time.sleep(random.uniform(0.5, 2.0))

    try:
        session = requests.Session()

        if YT_DLP_PROXY:
            session.proxies = {"http": YT_DLP_PROXY, "https": YT_DLP_PROXY}

        response = session.get(
            url,
            headers=headers,
            timeout=(10, 30),
            stream=True,
            allow_redirects=True,
            verify=True,
        )

        response.raise_for_status()

        # Check content type to ensure it's an image
        content_type = response.headers.get("content-type", "").lower()
        if not content_type.startswith("image/"):
            logger.error(
                f"URL does not point to an image. Content-Type: {content_type}"
            )
            return False

        # Check file size to prevent downloading extremely large files
        content_length = response.headers.get("content-length")
        if content_length:
            file_size = int(content_length)
            max_size = 50 * 1024 * 1024  # 50MB limit for images
            if file_size > max_size:
                logger.error(f"Image file too large: {file_size / 1024 / 1024:.2f}MB")
                return False

        # Download the image in chunks
        total_size = 0
        chunk_size = 8192  # 8KB chunks

        with open(image_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # Filter out keep-alive chunks
                    f.write(chunk)
                    total_size += len(chunk)

                    # Check size during download
                    if total_size > 50 * 1024 * 1024:  # 50MB limit
                        f.close()
                        image_path.unlink()  # Delete partial file
                        logger.error("Image file too large during download")
                        return False

        # Verify the file was downloaded successfully
        if not image_path.exists() or image_path.stat().st_size == 0:
            logger.error("Failed to download image or file is empty")
            return False

        return True

    except requests.exceptions.RequestException as e:
        # Clean up partial file if it exists
        if image_path.exists():
            image_path.unlink()
        return False
    except Exception as e:
        # Clean up partial file if it exists
        if image_path.exists():
            image_path.unlink()
        return False
