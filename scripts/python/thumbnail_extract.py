import time
from loguru import logger
from dotenv import load_dotenv

from src.lib.consts import WEBSITES
from src.lib.enums import VideoStatus
from src.lib.models import Video
from src.crud.video_crud import VideoCrud
from src.service.s1_fetch import fetch_video_urls
from src.lib.schemas import StorePath

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


if __name__ == "__main__":
    logger.info("🚀 Started")
    search_and_add_videos()
    logger.info("🎉 All done")
