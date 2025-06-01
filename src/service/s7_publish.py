import traceback

from loguru import logger
from sqlalchemy.orm import Session

from src.lib.connection import engine
from src.lib.consts import VideoStatus, BigLanguage, DB_ERROR_LOG_LENGTH, TermType
from src.lib.models import Video
from src.utils.log_utils import init_logging
from src.utils.wp_utils import wp_get_terms_lang_map_id, wp_create_term, wp_link_terms, wp_link_posts, wp_create_post


def create_or_get_term(term: str, translations: dict, term_type: TermType, lang: BigLanguage) -> int:
    term_dict = wp_get_terms_lang_map_id(term, term_type, len(BigLanguage))
    if lang in term_dict:
        return term_dict[lang]

    link_map = {}
    for l in BigLanguage:
        if l in term_dict:
            link_map[l.short_code] = term_dict[l]
        else:
            link_map[l.short_code] = wp_create_term(translations.get((term, l)), term_type, l)

    logger.info(f"Created all language for [{term_type}] [{term}]")

    wp_link_terms(link_map, term_type)
    logger.info(f"Linked all language for [{term_type}] [{term}]")

    return link_map[lang.short_code]


def create_post(video: Video, lang: BigLanguage) -> dict:
    tag_ids = category_ids = []

    term_translations = {(t.term, t.lang): t.translation for t in video.terms}

    for t in video.terms.items():
        if t.type == TermType.tag:
            tag_ids.append(create_or_get_term(t.term, term_translations, t.type, lang))
        else:
            category_ids.append(create_or_get_term(t.term, term_translations, t.type, lang))

    return wp_create_post(video, lang, tag_ids, category_ids)


def publish_video_to_wordpress(video: Video):
    lang_post_maps = {}
    for lang in BigLanguage:
        post = create_post(video, lang)

        lang_post_maps[lang.short_code] = post["id"]
        logger.info(f"✅ [{lang.short_code}] post created with ID: {post['id']}")

    if len(lang_post_maps) > 1:
        link_result = wp_link_posts(lang_post_maps)
        logger.info(f"✅ Posts linked: {link_result}")


def process_pending_videos(batch_size=10):
    last_id = 0
    while True:
        with Session(engine) as session:
            pending_videos = session.query(Video).filter(Video.status == VideoStatus.uploaded,
                                                         Video.id > last_id).limit(batch_size).all()
            if not pending_videos:
                break

            for video in pending_videos:
                try:
                    publish_video_to_wordpress(video)
                    video.status = VideoStatus.published
                    logger.info(f"Successfully published video {video.id}")
                except Exception as e:
                    video.status = VideoStatus.failed_published
                    video.failed_reason = str(e)[:DB_ERROR_LOG_LENGTH]
                    logger.error(f"Failed to publish video {video.id}: {str(e)}")
                    traceback.print_exc()

                session.commit()


if __name__ == "__main__":
    init_logging("publish")
    process_pending_videos()
