import os
import time
import tempfile
from pathlib import Path
from typing import List
from loguru import logger
from b2sdk.v2 import B2Api, InMemoryAccountInfo
from dotenv import load_dotenv

from src.lib.config import (
    WORKS_DIR,
    B2_APPLICATION_KEY_ID,
    B2_APPLICATION_KEY,
    B2_BUCKET_NAME,
)
from src.lib.consts import WEBSITES
from src.lib.enums import VideoStatus, ThumbnailStatus
from src.lib.models import Video
from src.crud.video_crud import VideoCrud
from src.service.s1_fetch import fetch_video_urls
from src.utils.download_utils import download_image
from src.lib.schemas import StorePath

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


def search_and_add_videos():
    """Search for videos using titles as keywords and add all found links to database"""
    logger.info("🔍 Starting video search and database population...")

    last_id = 14008
    total_processed = 0
    total_added = 0
    total_updated = 0

    while True:
        # Get batch of videos from database
        videos = VideoCrud.batch_get(
            last_id=last_id,
            batch_size=BATCH_SIZE,
        )

        if not videos:
            logger.info("No more videos to process for search")
            break

        logger.info(f"Processing batch of {len(videos)} videos for search")

        for video in videos:
            try:
                if video.thumbnail_url:
                    continue

                logger.info(f"🔍 【{video.id}】Searching with title: {video.title}")

                # Use video title as keyword to search for all related videos
                search_results = fetch_video_urls(video.title, page=1)
                sites = search_results.get("data", [])

                videos_to_update = []

                for site in sites:
                    if not site.get("links"):
                        continue

                    host = site["site"]["host"]
                    website_info = WEBSITES.get(host)
                    if not website_info:
                        logger.error(f"❌ Can not find website from {host}")
                        continue

                    id_extractor = website_info[1]()
                    if not id_extractor:
                        logger.error(f"❌ Can not find a extractor for host {host}")
                        continue

                    for link in site["links"]:
                        title = link.get("title")
                        url = link.get("url")
                        thumbnail_url = link.get("image", "")

                        if not title or not url:
                            continue

                        # Extract original_id for this link
                        original_id = id_extractor.get(url)
                        if not original_id:
                            logger.error(f"❌ Can not find a id from: {url}")
                            continue

                        # Create video entry for all links
                        new_video = Video(
                            title=title,
                            url=url,
                            thumbnail_url=thumbnail_url or "",
                            original_id=original_id,
                            host=host,
                            status=VideoStatus.fetched,
                            keyword=video.keyword,  # Use search video's keyword
                            author_name=link.get("channel", {}).get("name", ""),
                            author_url=link.get("channel", {}).get("url", ""),
                            store_dir=StorePath.build_prefix(host, original_id),
                        )
                        videos_to_update.append(new_video)

                added, updated = VideoCrud.batch_add_or_update(videos_to_update)
                logger.info(
                    f"📋 【{video.id}】Added [{added}], Updated [{updated}] from {len(videos_to_update)} unique videos"
                )

                total_processed += 1
                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                logger.error(f"❌ 【{video.id}】Error searching: {e}")
                continue

        last_id = videos[-1].id if videos else last_id

    logger.info(
        f"🔍 Search completed. Processed: {total_processed}, Added: {total_added}, Updated: {total_updated}"
    )


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

    last_id = 0
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
                if status not in [VideoStatus.fetched, VideoStatus.failed]
            ],
        )

        if not videos:
            logger.info("No more videos to process for thumbnail download")
            break

        # Filter videos that have thumbnail URLs and need processing
        videos_to_process = [
            video
            for video in videos
            if video.thumbnail_url
            and video.thumbnail_status == ThumbnailStatus.pending.value
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


def main():
    """Main function that executes both phases of thumbnail processing"""
    logger.info("🚀 Starting thumbnail processing workflow")

    # Phase 1: Search and add videos using titles as keywords
    logger.info("📋 Phase 1: Searching and adding videos to database")
    search_and_add_videos()

    # Phase 2: Download and upload thumbnails
    logger.info("📋 Phase 2: Downloading and uploading thumbnails")
    download_and_update_thumbnails()

    logger.info("🎉 Thumbnail processing workflow completed!")


if __name__ == "__main__":
    main()
