import asyncio
import sys
import time
import traceback
from collections import defaultdict

from loguru import logger
from sqlalchemy.cyextension.collections import OrderedSet

from src.crud.video_crud import VideoCrud
from src.lib.enums import Language, VideoStatus
from src.lib.models import Video
from src.utils.file_utils import rm_video
from src.utils.log_utils import init_logging
from src.utils.translate_utils import translate_texts


def translate_video(video: Video):
    title_translations = defaultdict()
    tag_translations = defaultdict()
    category_translations = defaultdict()

    categories = OrderedSet(video.categories)
    categories.add(video.keyword)

    for lang in Language:
        translated = translate_texts([video.title] + video.tags + list(categories), lang)

        title_translations[lang.short_code] = translated[0]
        tag_translations[lang.short_code] = translated[1:len(video.tags) + 1]
        category_translations[lang.short_code] = translated[len(video.tags) + 1:]

    VideoCrud.update({
        "id": video.id,
        "title_translations": title_translations,
        "tag_translations": tag_translations,
        "category_translations": category_translations,
        "status": VideoStatus.meta_translated,
        "failed_reason": "",
    })


def translate_meta_infos(batch_size: int = 10, host: str = ""):
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.vtt_translated, host)
        if not videos:
            logger.info("All meta translated, sleeping for 5 minutes")
            time.sleep(5 * 60)
            continue

        last_id = videos[-1].id
        for video in videos:
            try:
                translate_video(video)
                logger.info(f"[{video.id} | {video.host} | {video.original_id}] translated")
            except Exception as e:
                VideoCrud.update_status(video.id, VideoStatus.failed, VideoStatus.meta_translated.log(e))
                exception_count += 1
                if exception_count >= 3:
                    raise e
                traceback.print_exc()
                asyncio.run(rm_video(video))


if __name__ == "__main__":
    init_logging("meta_translate")

    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    host = sys.argv[2] if len(sys.argv) > 2 else ""

    translate_meta_infos(batch_size, host)
    logger.info("All metas translated")
