import traceback
from collections import defaultdict

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.consts import DB_ERROR_LOG_LENGTH
from src.lib.enums import VideoStatus, Language
from src.lib.models import Video
from src.utils.log_utils import init_logging
from src.utils.translate_utils import translate_texts


def translate_video(video: Video):
    title_translations = defaultdict()
    tags_translations = defaultdict()
    categories_translations = defaultdict()

    for lang in Language:
        translated = translate_texts([video.title] + video.tags + video.categories, lang)

        title_translations[lang.short_code] = translated[0]
        tags_translations[lang.short_code] = translated[1:len(video.tags) + 1]
        categories_translations[lang.short_code] = translated[len(video.category_translations) + 1:]

    VideoCrud.update({
        "id": video.id,
        "title_translations": title_translations,
        "tags_translations": tags_translations,
        "categories_translations": categories_translations
    })


def translate_meta_infos(batch_size: int = 10):
    last_id = 0
    exception_count = 0
    
    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.subtitled)
        if not videos:
            break

        for video in videos:
            try:
                translate_video(video)
                logger.info(f"[{video.id}: {video.title}] translated")
            except Exception as e:
                VideoCrud.update_status(video.id, VideoStatus.failed_meta_translated, str(e)[:DB_ERROR_LOG_LENGTH])
                logger.error(f"[{video.id}: {video.title}] failed to translate: {str(e)}")
                exception_count += 1
                if exception_count >= 3:
                    raise e
                traceback.print_exc()

        last_id = videos[-1].id


if __name__ == "__main__":
    init_logging("meta_translate")
    translate_meta_infos()
