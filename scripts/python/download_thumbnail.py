import csv
import json
import os
import time
import tempfile
from pathlib import Path
from loguru import logger
import yt_dlp
import requests
from b2sdk.v2 import B2Api, InMemoryAccountInfo
from dotenv import load_dotenv
from tenacity import retry, stop_after_attempt, wait_fixed

from src.lib.config import WORKS_DIR
from src.lib.consts import WEBSITES

load_dotenv()

# B2 settings - Load from environment variables
PROXY_ENABLED = os.getenv("PROXY_ENABLED", "false").lower() == "true"
PROXY_URL = os.getenv("PROXY_URL", "socks5://127.0.0.1:9150")
B2_APPLICATION_KEY_ID = os.getenv("B2_APPLICATION_KEY_ID")
B2_APPLICATION_KEY = os.getenv("B2_APPLICATION_KEY")
B2_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")

CSV_FILE = WORKS_DIR / "videos_rows.csv"
LAST_ID_FILE = WORKS_DIR / "last_thumbnail_id.txt"


class B2Client:
    def __init__(self, key_id: str, application_key: str, bucket_name: str):
        self.info = InMemoryAccountInfo()
        self.api = B2Api(self.info)
        self.api.authorize_account("production", key_id, application_key)
        self.bucket = self.api.get_bucket_by_name(bucket_name)

    def upload_file(self, file_path: Path, b2_key: str) -> str:
        """Upload a file to B2 and return the public URL"""
        uploaded_file = self.bucket.upload_local_file(
            local_file=str(file_path), file_name=b2_key
        )
        return f"https://play.luckvideos.com/{b2_key}"


@retry(wait=wait_fixed(2), stop=stop_after_attempt(3), reraise=True)
def download_thumbnail(url: str, output_path: Path) -> bool:
    """Download thumbnail using yt-dlp and convert to webp"""
    ydl_opts = {
        "writethumbnail": "best",
        "outtmpl": str(output_path.with_suffix("")),
        "skip_download": True,  # Skip downloading video/audio
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "convert_thumbnails": "webp",  # Convert thumbnails to webp format
    }

    # Add proxy if enabled
    if PROXY_ENABLED:
        ydl_opts["proxy"] = PROXY_URL

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract info first to check if thumbnail is available
        info = ydl.extract_info(url, download=False)
        if not info:
            logger.error(f"No info extracted for {url}")
        else:
            # Download only the thumbnail
            ydl.download([url])


def read_last_id() -> int:
    """Read the last processed ID from file"""
    try:
        with open(LAST_ID_FILE, "r") as f:
            return int(f.read().strip())
    except FileNotFoundError:
        return 0


def write_last_id(last_id: int):
    """Write the last processed ID to file"""
    # Ensure the directory exists
    Path(LAST_ID_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(LAST_ID_FILE, "w") as f:
        f.write(str(last_id))


def process_videos():
    """Process videos from CSV that meet the criteria"""
    # Validate B2 settings
    if not all([B2_APPLICATION_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_NAME]):
        logger.info("❌ B2 settings not configured!")
        logger.info("Please set the following environment variables:")
        logger.info("  - B2_APPLICATION_KEY_ID")
        logger.info("  - B2_APPLICATION_KEY")
        logger.info("  - B2_BUCKET_NAME")
        return

    # Initialize B2 client
    b2_client = B2Client(B2_APPLICATION_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_NAME)

    # Read last processed ID
    last_id = read_last_id()
    logger.info(f"Starting from ID: {last_id}")

    # Read CSV and filter videos
    videos_to_process = []

    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                video_id = int(row.get("id", 0))
                status = row.get("status", "")

                # Check if video meets criteria
                if video_id > last_id and status != "fetched" and status != "failed":
                    videos_to_process.append(row)

                # order by video id
                videos_to_process.sort(key=lambda x: int(x["id"]))
            except (ValueError, KeyError):
                continue

    logger.info(f"Found {len(videos_to_process)} videos to process")

    max_id = last_id
    # Process each video
    for row in videos_to_process:
        video_id = int(row["id"])
        url = row.get("url", "")
        host = row.get("host", "")
        original_id = row.get("original_id", "")

        if not url or not host:
            logger.info(f"⚠️ Skipping video {video_id}: missing required data")
            continue

        short_name, _ = WEBSITES.get(host)
        if not short_name:
            logger.info(f"⚠️ Skipping video {video_id}: unknown host {host}")
            continue

        logger.info(f"📥 Processing video {video_id}: {url}")

        # Download thumbnail
        with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp_file:
            tmp_path = Path(tmp_file.name)

        try:
            download_thumbnail(url, tmp_path)
        except Exception as e:
            logger.error(f"❌ Failed to download thumbnail for video {video_id}: {e}")

        if not tmp_path.exists() or tmp_path.stat().st_size == 0:
            logger.error(f"❌ Failed to download thumbnail for video {video_id}")
            continue

        b2_key = f"{short_name}/{original_id[:2]}/{original_id}/thumbnail.webp"
        logger.info(f"📤 Uploading thumbnail to B2: {b2_key}")
        try:
            thumbnail_url = b2_client.upload_file(tmp_path, b2_key)
            logger.info(f"✅ Thumbnail uploaded: {thumbnail_url}")
        except Exception as e:
            logger.info(f"❌ Failed to upload thumbnail: {e}")
        finally:
            # Clean up temp file
            tmp_path.unlink(missing_ok=True)

        max_id = video_id
        write_last_id(max_id)
        time.sleep(1)

    logger.info(f"✅ Updated last_id to: {max_id}")


def main():
    process_videos()


if __name__ == "__main__":
    main()
