import traceback

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.consts import DB_ERROR_LOG_LENGTH
from src.lib.enums import VideoStatus, Language, TermType
from src.lib.models import Video
from src.lib.schemas import TaxonomyIn
from src.utils.log_utils import init_logging
from src.utils.wp_utils import wp_link_posts, wp_create_post, wp_batch_get_or_add_terms


def publish_video(video: Video):
    lang_post_maps = {}
    tag_ids = wp_batch_get_or_add_terms(TaxonomyIn(taxonomy=TermType.tags, translations=video.tag_translations))
    logger.info(f"[{video.id}] added tags")

    category_ids = wp_batch_get_or_add_terms(
        TaxonomyIn(taxonomy=TermType.categories, translations=video.category_translations))
    logger.info(f"[{video.id}] added categories")

    for lang in Language:
        post = wp_create_post(video, lang, tag_ids[lang.short_code], category_ids[lang.short_code])
        lang_post_maps[lang.short_code] = post["id"]

    if len(lang_post_maps) > 1:
        wp_link_posts(lang_post_maps)
    logger.info(f"[{video.id}] added and linked")
    VideoCrud.update_status(video.id, VideoStatus.published)


def process_pending_videos(batch_size=10):
    last_id = 0
    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.uploaded)
        if not videos:
            break

        for video in videos:
            try:
                publish_video(video)
                logger.info(f"[{video.id}] published")
            except Exception as e:
                VideoCrud.update_status(video.id, VideoStatus.failed_published, str(e)[:DB_ERROR_LOG_LENGTH])
                logger.error(f"[{video.id}] failed to translate: {str(e)}")
                traceback.print_exc()

        last_id = videos[-1].id


if __name__ == "__main__":
    init_logging("publish")
    process_pending_videos()
