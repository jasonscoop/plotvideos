import time
import traceback
from typing import Optional, Tuple

from loguru import logger

from crud.term_crud import TermCrud
from crud.video_crud import VideoCrud
from crud.video_title_translation_crud import TitleTranslationCrud
from core.config import S6_TRANSLATE_META_BATCH_SIZE
from core.enums import VideoStatus
from core.languages import Language
from core.models import Video
from utils.signal_utils import setup_graceful_shutdown, should_stop
from utils.translate_utils import translate_list


def translate_video(video: Video, languages):
    title_translations = {}
    all_terms = [video.keyword.name] + video.tags + video.categories
    all_translations = TermCrud.get_translations_map(all_terms)

    for lang in languages:
        existing_translations = all_translations.get(lang.code, {})
        terms_to_translate = [
            term for term in all_terms if term not in existing_translations
        ]

        texts_to_translate = [video.title] + terms_to_translate
        new_translations = translate_list(texts_to_translate, lang)

        title_translations[lang.code] = new_translations[0]
        for term, translation in zip(terms_to_translate, new_translations[1:]):
            TermCrud.create(term, lang.code, translation)

    TitleTranslationCrud.batch_create_or_update(video.id, title_translations)

    VideoCrud.update(
        {
            "id": video.id,
            "status": VideoStatus.meta_translated,
            "failed_reason": "",
        }
    )


def process_batch(last_id: Optional[int]) -> Tuple[bool, Optional[int]]:
    """Translate metadata for one batch of vtt-translated videos. Returns (had_work, next_last_id)."""
    languages = Language.get_all()
    videos = VideoCrud.batch_get(last_id, S6_TRANSLATE_META_BATCH_SIZE, VideoStatus.vtt_translated)
    if not videos:
        return False, None

    exception_count = 0
    for video in videos:
        try:
            translate_video(video, languages)
            logger.info(
                f"[{video.id} | {video.host}] translated"
            )
        except Exception as e:
            VideoCrud.record_failure(
                video.id, VideoStatus.meta_translated.log(e)
            )
            exception_count += 1
            traceback.print_exc()
            if exception_count >= 3:
                raise e

    return True, videos[-1].id


def translate_meta_infos():
    setup_graceful_shutdown()
    last_id = None

    while not should_stop():
        had_work, last_id = process_batch(last_id)
        if not had_work:
            logger.info("All meta translated, sleeping for 5 minutes")
            time.sleep(5 * 60)
            last_id = None
