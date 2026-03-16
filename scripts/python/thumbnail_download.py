import os
import time
import tempfile
from pathlib import Path
from typing import List
from loguru import logger
from b2sdk.v2 import B2Api, InMemoryAccountInfo
from dotenv import load_dotenv

from crawler.core.config import (
    WORKS_DIR,
    B2_APPLICATION_KEY_ID,
    B2_APPLICATION_KEY,
    B2_BUCKET_NAME,
)
from crawler.core.consts import WEBSITES
from crawler.core.enums import VideoStatus, ThumbnailStatus
from crawler.core.models import Video
from crawler.crud.video_crud import VideoCrud
from crawler.service.s1_fetch import fetch_video_urls
from crawler.utils.download_utils import download_image
from crawler.core.schemas import StorePath

load_dotenv()

# Configuration

BATCH_SIZE = 50


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


def download_and_update_thumbnails():
    """Rescan database to download thumbnails and update their status"""
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

    logger.info("📥 Starting thumbnail download and status update...")

    last_id = 27555
    total_processed = 0
    total_uploaded = 0

    while True:
        # Get batch of videos from database
        videos = VideoCrud.batch_get(
            last_id=last_id,
            batch_size=BATCH_SIZE,
            status=[
                status
                for status in VideoStatus
                if status != VideoStatus.fetched
            ],
        )

        if not videos:
            logger.info("No more videos to process for thumbnail download")
            break

        # Filter videos that have thumbnail URLs and need processing
        videos_to_process = [
            video
            for video in videos
            if video.thumbnail_status == ThumbnailStatus.pending.value
        ]

        logger.info(
            f"Processing {len(videos_to_process)} videos for thumbnail download"
        )

        max_id = last_id
        for video in videos_to_process:

            website_info = WEBSITES.get(video.host)
            if website_info is None:
                logger.info(f"⚠️ 【{video.id}】Unknown host {video.host}")
                max_id = video.id
                continue

            logger.info(
                f"📥 【{video.id}】Downloading thumbnail: {video.thumbnail_url}"
            )

            if not video.thumbnail_url:
                VideoCrud.update(
                    {"id": video.id, "thumbnail_status": ThumbnailStatus.failed.value}
                )
                max_id = video.id
                continue

            # Download thumbnail
            with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)

            try:
                success = download_image(video.thumbnail_url, tmp_path)
                if not success:
                    logger.error(f"❌ 【{video.id}】Failed to download thumbnail")
                    # Update thumbnail status to failed
                    VideoCrud.update(
                        {
                            "id": video.id,
                            "thumbnail_status": ThumbnailStatus.failed.value,
                        }
                    )
                    max_id = video.id
                    continue
            except Exception as e:
                logger.error(f"❌ 【{video.id}】Failed to download thumbnail: {e}")
                # Update thumbnail status to failed
                VideoCrud.update(
                    {"id": video.id, "thumbnail_status": ThumbnailStatus.failed.value}
                )
                max_id = video.id
                continue

            if not tmp_path.exists() or tmp_path.stat().st_size == 0:
                logger.error(
                    f"❌ 【{video.id}】Failed to download thumbnail, file size is 0"
                )
                # Update thumbnail status to failed
                VideoCrud.update(
                    {"id": video.id, "thumbnail_status": ThumbnailStatus.failed.value}
                )
                max_id = video.id
                continue

            # Upload to B2 storage
            b2_key = video.store_path.thumbnail_s3_key
            try:
                b2_thumbnail_url = b2_client.upload_file(tmp_path, b2_key)
                logger.info(
                    f"✅ 【{video.id}】Thumbnail uploaded to B2: {b2_thumbnail_url}"
                )

                # Update only thumbnail status in database
                VideoCrud.update(
                    {
                        "id": video.id,
                        "thumbnail_status": ThumbnailStatus.downloaded.value,
                    }
                )
                total_uploaded += 1

            except Exception as e:
                logger.error(f"❌ 【{video.id}】Failed to upload thumbnail: {e}")
                # Update thumbnail status to failed
                VideoCrud.update(
                    {"id": video.id, "thumbnail_status": ThumbnailStatus.failed.value}
                )
            finally:
                tmp_path.unlink(missing_ok=True)

            max_id = video.id
            total_processed += 1
            time.sleep(1)

        # Update last processed ID for next batch
        last_id = max_id if videos_to_process else videos[-1].id

    logger.info(
        f"📥 Thumbnail download completed. Total processed: {total_processed}, Total uploaded: {total_uploaded}"
    )


if __name__ == "__main__":
    logger.info("🚀 Started")
    download_and_update_thumbnails()
    logger.info("🎉 Done")
