import os
import time
import tempfile
from pathlib import Path
from typing import List
from loguru import logger
from b2sdk.v2 import B2Api, InMemoryAccountInfo
from dotenv import load_dotenv
import yt_dlp

from crawler.lib.config import (
    WORKS_DIR,
    B2_APPLICATION_KEY_ID,
    B2_APPLICATION_KEY,
    B2_BUCKET_NAME,
    YT_DLP_PROXY,
)
from crawler.lib.consts import WEBSITES
from crawler.lib.enums import VideoStatus, ThumbnailStatus
from crawler.lib.models import Video
from crawler.crud.video_crud import VideoCrud
from crawler.service.s1_fetch import fetch_video_urls
from crawler.utils.download_utils import download_image
from crawler.lib.schemas import StorePath

load_dotenv()

# Configuration

BATCH_SIZE = 50


def download_thumbnail_with_ytdlp(video_url: str) -> tuple[bool, str]:
    """Download thumbnail using yt-dlp without downloading the video"""
    try:
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "writesubtitles": False,
            "writeautomaticsub": False,
            "proxy": YT_DLP_PROXY,
            "writethumbnail": True,
            "skip_download": True,  # Don't download the video, only thumbnail
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info to get thumbnail URL
            info = ydl.extract_info(video_url, download=False)

            if not info:
                logger.error(f"Failed to extract info from {video_url}")
                return False, ""

            # Get the best thumbnail URL from the thumbnails list
            thumbnails = info.get("thumbnails", [])
            if not thumbnails:
                # Fallback to single thumbnail field
                thumbnail_url = info.get("thumbnail")
                if not thumbnail_url:
                    logger.error(f"No thumbnail URL found for {video_url}")
                    return False, ""
                logger.info(f"Found thumbnail URL (fallback): {thumbnail_url}")
            else:
                # Find the best quality thumbnail (highest resolution)
                best_thumbnail = thumbnails[0]
                thumbnail_url = best_thumbnail.get("url")
                if not thumbnail_url:
                    logger.error(f"No URL in best thumbnail for {video_url}")
                    return False, ""

                logger.info(f"Found best thumbnail URL: {thumbnail_url}")

            # Download the thumbnail using the regular download_image function
            # success = download_image(thumbnail_url, thumbnail_path)
            return True, thumbnail_url

    except Exception as e:
        logger.error(f"Failed to download thumbnail with yt-dlp: {e}")
        return False, ""


def download_and_update_thumbnails():
    """Rescan database to download thumbnails using yt-dlp and update their status"""
    # Validate B2 settings
    if not all([B2_APPLICATION_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_NAME]):
        logger.info("❌ B2 settings not configured!")
        logger.info("Please set the following environment variables:")
        logger.info("  - B2_APPLICATION_KEY_ID")
        logger.info("  - B2_APPLICATION_KEY")
        logger.info("  - B2_BUCKET_NAME")
        return

    logger.info("📥 Starting thumbnail download with yt-dlp and status update...")

    last_id = 28484
    total_processed = 0
    total_uploaded = 0

    while True:
        # Get batch of videos from database
        videos = VideoCrud.batch_get(
            last_id=last_id,
            batch_size=BATCH_SIZE,
            status=[
                status for status in VideoStatus if status not in [VideoStatus.failed]
            ],
        )

        if not videos:
            logger.info("No more videos to process for thumbnail download")
            break

        # Filter videos that have thumbnail URLs and need processing
        videos_to_process = [
            video
            for video in videos
            if video.thumbnail_url == ""
            and video.thumbnail_status
            in [ThumbnailStatus.pending.value, ThumbnailStatus.failed.value]
        ]

        logger.info(
            f"Thumbnailing {len(videos_to_process)} videos between {videos[0].id}-{videos[-1].id}"
        )

        max_id = last_id
        for video in videos_to_process:

            website_info = WEBSITES.get(video.host)
            if website_info is None:
                logger.info(f"⚠️ 【{video.id}】Unknown host {video.host}")
                max_id = video.id
                continue

            logger.info(
                f"📥 【{video.id}】Downloading thumbnail with yt-dlp: {video.url}"
            )

            if not video.url:
                VideoCrud.update(
                    {"id": video.id, "thumbnail_status": ThumbnailStatus.failed.value}
                )
                max_id = video.id
                continue

            try:
                success, original_thumbnail_url = download_thumbnail_with_ytdlp(
                    video.url
                )
                if not success:
                    logger.error(
                        f"❌ 【{video.id}】Failed to download thumbnail with yt-dlp"
                    )
                    # Update thumbnail status to failed
                    VideoCrud.update(
                        {
                            "id": video.id,
                            "thumbnail_status": ThumbnailStatus.failed.value,
                        }
                    )
                    max_id = video.id
                    continue
                else:
                    VideoCrud.update(
                        {
                            "id": video.id,
                            "thumbnail_url": original_thumbnail_url,
                        }
                    )
            except Exception as e:
                logger.error(
                    f"❌ 【{video.id}】Failed to download thumbnail with yt-dlp: {e}"
                )
                # Update thumbnail status to failed
                VideoCrud.update(
                    {"id": video.id, "thumbnail_status": ThumbnailStatus.failed.value}
                )
                max_id = video.id
                continue

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
