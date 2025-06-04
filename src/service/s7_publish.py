import sys
import traceback

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.consts import DB_ERROR_LOG_LENGTH
from src.lib.enums import VideoStatus, Language, TermType
from src.lib.models import Video
from src.lib.schemas import TaxonomyIn
from src.utils.log_utils import init_logging
from src.utils.wp_utils import wp_link_posts, wp_create_post, wp_batch_get_or_add_terms, wp_get_or_create_user


def publish_video(video: Video):
    lang_post_maps = {}
    tag_ids = wp_batch_get_or_add_terms(TaxonomyIn(taxonomy=TermType.tags, translations=video.tag_translations))
    logger.info(f"[{video.id} | {video.host} | {video.original_id}] added tags")

    category_ids = wp_batch_get_or_add_terms(
        TaxonomyIn(taxonomy=TermType.categories, translations=video.category_translations))
    logger.info(f"[{video.id} | {video.host} | {video.original_id}] added categories")

    author_id = wp_get_or_create_user(video.author_name, video.author_url)

    for lang in Language:
        post = wp_create_post(video, author_id, lang, tag_ids.get(lang.short_code, []),
                              category_ids.get(lang.short_code, []))
        lang_post_maps[lang.short_code] = post["id"]

    if len(lang_post_maps) > 1:
        wp_link_posts(lang_post_maps)
    logger.info(f"[{video.id} | {video.host} | {video.original_id}] post added and linked")
    VideoCrud.update_status(video.id, VideoStatus.published)


def publish_videos(batch_size=10, host: str = ""):
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.uploaded, host)
        if not videos:
            break

        last_id = videos[-1].id
        for video in videos:
            try:
                publish_video(video)
                logger.info(f"[{video.id} | {video.host} | {video.original_id}] published")
            except Exception as e:
                reason = str(e)[:DB_ERROR_LOG_LENGTH]
                VideoCrud.update_status(video.id, VideoStatus.failed_published, reason)
                exception_count += 1
                if exception_count >= 3:
                    raise e
                traceback.print_exc()


if __name__ == "__main__":
    init_logging("publish")
    host = sys.argv[1] if len(sys.argv) > 1 else ""
    publish_videos(10, host)
    logger.info("All published")
