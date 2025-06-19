import time
import traceback
from collections import defaultdict

from loguru import logger
from requests.exceptions import HTTPError

from src.crud.language_crud import LanguageCrud
from src.crud.term_crud import TermCrud
from src.crud.video_crud import VideoCrud
from src.lib.enums import VideoStatus
from src.lib.models import Video
from src.utils.file_utils import rm_video
from src.utils.translate_utils import translate_texts2, translate_texts1


def translate_video(video: Video, languages):
    title_translations = defaultdict(dict)
    all_terms = [video.keyword] + video.tags + video.categories
    all_translations = TermCrud.get_translations(all_terms)

    for lang in languages:
        existing_translations = all_translations.get(lang.code, {})
        terms_to_translate = [term for term in all_terms if term not in existing_translations]

        # Combine title and new terms for a single translation request
        texts_to_translate = [video.title] + terms_to_translate
        new_translations = [video.title]
        if texts_to_translate:
            try:
                new_translations = translate_texts1(texts_to_translate, lang)
                logger.info(f"[{video.id} | {video.host} | {video.original_id}] translated with translator1")
            except HTTPError as e:
                new_translations = translate_texts2(texts_to_translate, lang)
                logger.warning(
                    f"[{video.id} | {video.host} | {video.original_id}] translated with translator2 (fallback)")

        title_translations[lang.code] = new_translations[0]
        for term, translation in zip(terms_to_translate, new_translations[1:]):
            TermCrud.create(term, lang.code, translation)

    VideoCrud.update({
        "id": video.id,
        "title_translations": title_translations,
        "status": VideoStatus.meta_translated,
        "failed_reason": "",
    })


def translate_meta_infos(batch_size: int = 10, host: str = ""):
    last_id = 0
    exception_count = 0
    languages = LanguageCrud.get_all()

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.vtt_translated, host)
        if not videos:
            logger.info("All meta translated, sleeping for 5 minutes")
            time.sleep(5 * 60)
            last_id = 0
            languages = LanguageCrud.get_all()
            continue

        last_id = videos[-1].id
        for video in videos:
            try:
                translate_video(video, languages)
                logger.info(f"[{video.id} | {video.host} | {video.original_id}] translated")
            except Exception as e:
                VideoCrud.update_status(video.id, VideoStatus.failed, VideoStatus.meta_translated.log(e))
                exception_count += 1
                traceback.print_exc()
                rm_video(video)
                if exception_count >= 3:
                    raise e
