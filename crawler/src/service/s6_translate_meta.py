import time
import traceback

from loguru import logger

from src.crud.language_crud import LanguageCrud
from src.crud.term_crud import TermCrud
from src.crud.video_crud import VideoCrud
from src.crud.video_title_translation_crud import TitleTranslationCrud
from src.lib.config import S6_TRANSLATE_META_BATCH_SIZE
from src.lib.enums import VideoStatus
from src.lib.models import Video
from src.utils.nllb_utils import nllb_translate


def translate_video(video: Video, languages):
    title_translations = {}
    all_terms = [video.keyword.name] + video.tags + video.categories
    all_translations = TermCrud.get_translations(all_terms)

    for lang in languages:
        existing_translations = all_translations.get(lang.code, {})
        terms_to_translate = [
            term for term in all_terms if term not in existing_translations
        ]

        texts_to_translate = [video.title] + terms_to_translate
        new_translations = nllb_translate(texts_to_translate, lang)
        logger.info(
            f"[{video.id} | {video.host} | {video.original_id}] translated with NLLB"
        )

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


def translate_meta_infos(host: str = ""):
    last_id = None
    exception_count = 0
    languages = LanguageCrud.get_all()

    while True:
        videos = VideoCrud.batch_get(
            last_id, S6_TRANSLATE_META_BATCH_SIZE, VideoStatus.vtt_translated, host
        )
        if not videos:
            logger.info("All meta translated, sleeping for 5 minutes")
            time.sleep(5 * 60)
            last_id = None
            languages = LanguageCrud.get_all()
            continue

        last_id = videos[-1].id
        for video in videos:
            try:
                translate_video(video, languages)
                logger.info(
                    f"[{video.id} | {video.host} | {video.original_id}] translated"
                )
            except Exception as e:
                VideoCrud.update_status(
                    video.id, VideoStatus.failed, VideoStatus.meta_translated.log(e)
                )
                exception_count += 1
                traceback.print_exc()
                if exception_count >= 3:
                    raise e
