import os
from pathlib import Path
from typing import Optional
from loguru import logger
from b2sdk.v2 import B2Api, InMemoryAccountInfo
from tenacity import retry, stop_after_attempt, wait_fixed

from crawler.lib.config import (
    B2_APPLICATION_KEY_ID,
    B2_APPLICATION_KEY,
    B2_BUCKET_NAME,
    B2_CDN_DOMAIN,
)
from crawler.lib.languages import Language
from crawler.lib.models import Video


class B2Client:
    def __init__(self, key_id: str, application_key: str, bucket_name: str):
        self.info = InMemoryAccountInfo()
        self.api = B2Api(self.info)
        self.api.authorize_account("production", key_id, application_key)
        self.bucket = self.api.get_bucket_by_name(bucket_name)
        self.bucket_name = bucket_name

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3), reraise=True)
    def upload_file(self, file_path: Path, b2_key: str) -> str:
        """Upload a file to B2 and return the public URL"""
        uploaded_file = self.bucket.upload_local_file(
            local_file=str(file_path), file_name=b2_key
        )
        return f"{B2_CDN_DOMAIN}/{b2_key}"

    @retry(wait=wait_fixed(2), stop=stop_after_attempt(3), reraise=True)
    def upload_directory(self, directory_path: Path, prefix: str) -> list[str]:
        """Upload all files in a directory to B2 with the given prefix"""
        uploaded_urls = []

        if not directory_path.exists():
            logger.warning(f"Directory {directory_path} does not exist")
            return uploaded_urls

        for file_path in directory_path.rglob("*"):
            if file_path.is_file():
                # Calculate relative path from directory
                relative_path = file_path.relative_to(directory_path)
                b2_key = f"{prefix}/{relative_path}".replace(
                    "\\", "/"
                )  # Ensure forward slashes

                try:
                    url = self.upload_file(file_path, b2_key)
                    uploaded_urls.append(url)
                    logger.debug(f"Uploaded {file_path} to {b2_key}")
                except Exception as e:
                    logger.error(f"Failed to upload {file_path} to {b2_key}: {e}")
                    raise e

        return uploaded_urls

    def upload_video_and_subtitles(
        self, video: Video, languages: list[Language]
    ) -> dict:
        """Upload video and subtitle files for a video, returns URLs"""
        results = {"video_url": None, "subtitle_urls": {}, "thumbnail_url": None}

        # Upload main video file using s3_key from schema
        if video.store_path.video.exists():
            results["video_url"] = self.upload_file(
                video.store_path.video, video.store_path.video_s3_key
            )
            logger.info(f"[{video.id}] Uploaded video to B2: {results['video_url']}")
        else:
            raise FileNotFoundError(f"Video file not found: {video.store_path.video}")

        # Upload subtitle files using s3_key pattern
        if video.store_path.translated_vtts.exists():
            for lang in languages:
                vtt_file = video.store_path.translated_vtts / f"{lang.code}.vtt"
                if vtt_file.exists():
                    # Use translated_s3_key as base and append language
                    vtt_b2_key = f"{video.store_path.translated_s3_key}{lang.code}.vtt"
                    results["subtitle_urls"][lang.code] = self.upload_file(
                        vtt_file, vtt_b2_key
                    )
                    logger.info(f"[{video.id}] Uploaded {lang.code} subtitle to B2")
                else:
                    logger.warning(
                        f"[{video.id}] Subtitle file for {lang.code} not found"
                    )

        # Upload thumbnail using s3_key from schema
        if video.store_path.thumbnail.exists():
            results["thumbnail_url"] = self.upload_file(
                video.store_path.thumbnail, video.store_path.thumbnail_s3_key
            )
            logger.info(f"[{video.id}] Uploaded thumbnail to B2")

        # Upload HLS directory (master.m3u8 + variant playlists + .ts segments)
        if video.store_path.hls_dir.exists():
            hls_urls = self.upload_directory(
                video.store_path.hls_dir, video.store_path.hls_s3_prefix
            )
            results["hls_urls"] = hls_urls
            logger.info(
                f"[{video.id}] Uploaded {len(hls_urls)} HLS files to B2"
            )

        return results


# Global B2 client instance
b2_client: Optional[B2Client] = None


def get_b2_client() -> B2Client:
    """Get or create the global B2 client instance"""
    global b2_client

    if b2_client is None:
        if not all([B2_APPLICATION_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_NAME]):
            raise ValueError(
                "B2 configuration is missing. Please set B2_APPLICATION_KEY_ID, B2_APPLICATION_KEY, and B2_BUCKET_NAME environment variables."
            )

        b2_client = B2Client(B2_APPLICATION_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_NAME)
        logger.info("B2 client initialized")

    return b2_client
