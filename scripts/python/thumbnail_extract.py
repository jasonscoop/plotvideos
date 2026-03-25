import time
import zlib
from loguru import logger
from dotenv import load_dotenv

from crawler.core.enums import VideoStatus
from crawler.core.models import Video
from crawler.crud.video_crud import VideoCrud
from crawler.service.s1_fetch import fetch_video_urls

load_dotenv()
BATCH_SIZE = 50


def search_and_add_videos():
    """Search for videos using titles as keywords and add all found links to database"""
    logger.info("🔍 Starting video search and database population...")

    last_id = 51664
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

                    for link in site["links"]:
                        title = link.get("title")
                        url = link.get("url")
                        thumbnail_url = link.get("image", "")

                        if not title or not url:
                            continue

                        new_video = Video(
                            title=title,
                            url=url,
                            url_crc32=zlib.crc32(url.encode()),
                            thumbnail_url=thumbnail_url or "",
                            host=host,
                            status=VideoStatus.fetched,
                            keyword_id=video.keyword_id,
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


if __name__ == "__main__":
    logger.info("🚀 Started")
    search_and_add_videos()
    logger.info("🎉 All done")
