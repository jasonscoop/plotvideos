from pathlib import Path
import random
import time
import subprocess
from typing import Optional
from loguru import logger
import yt_dlp
import requests
import ffmpeg
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
    if not url:
        logger.warning(f"No thumbnail URL provided: {image_path}")
        return False

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

    if url.startswith("//"):
        url = f"https:{url}"

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

        # Create temporary path for downloading
        temp_image_path = image_path.with_suffix(".temp")

        # Download the image in chunks to temporary file
        total_size = 0
        chunk_size = 8192  # 8KB chunks

        with open(temp_image_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # Filter out keep-alive chunks
                    f.write(chunk)
                    total_size += len(chunk)

                    # Check size during download
                    if total_size > 50 * 1024 * 1024:  # 50MB limit
                        f.close()
                        temp_image_path.unlink()  # Delete partial file
                        logger.error("Image file too large during download")
                        return False

        # Verify the file was downloaded successfully
        if not temp_image_path.exists() or temp_image_path.stat().st_size == 0:
            logger.error("Failed to download image or file is empty")
            if temp_image_path.exists():
                temp_image_path.unlink()
            return False

        # Check if the downloaded image is already WebP
        try:
            # Use ffprobe to check the format
            probe = ffmpeg.probe(str(temp_image_path))
            format_name = probe["format"]["format_name"]

            if "webp" in format_name.lower():
                # Already WebP, just move to final location
                temp_image_path.rename(image_path)
                logger.info(f"Image is already WebP format: {image_path}")
            else:
                # Convert to WebP using ffmpeg
                stream = ffmpeg.input(str(temp_image_path))
                stream = ffmpeg.output(
                    stream, str(image_path), vcodec="libwebp", quality=90
                )
                ffmpeg.run(stream, quiet=True, overwrite_output=True)

                # Remove temporary file
                temp_image_path.unlink()

                logger.info(
                    f"Successfully converted image from {format_name} to WebP: {image_path}"
                )

        except Exception as e:
            # If format checking or conversion fails, just move the original file
            temp_image_path.rename(image_path)
            logger.error(f"Failed to process image format, keeping original: {e}")
            return True

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
