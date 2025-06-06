import sys
import traceback
from concurrent.futures import ThreadPoolExecutor

import webvtt
from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.consts import DB_ERROR_LOG_LENGTH
from src.lib.enums import VideoStatus, Language
from src.lib.schemas import StorePath
from src.utils.log_utils import init_logging
from src.utils.translate_utils import translate_texts


def translate_and_save(lang, vtt_content, path, video):
    translated = translate_vtt_content(vtt_content, lang)
    translated_file = path.translated_vtts / f"{lang.short_code}.vtt"
    translated_file.write_text(translated)
    logger.info(f"[{video.id} | {video.host} | {video.original_id}] vtt translated '{lang.short_code}'")


def translate_vtt_content(vtt_content, lang) -> str:
    vtt = webvtt.from_string(vtt_content)
    texts = [c.text for c in vtt]
    translated_texts = translate_texts(texts, lang)

    for i, t in enumerate(translated_texts):
        vtt.captions[i].text = t

    return vtt.content


def process_subtitled_videos(batch_size: int = 10, host: str = ""):
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.meta_translated, host)
        if not videos:
            break

        last_id = videos[-1].id

        for video in videos:
            if len(video.subtitle_content.strip()) == 0:
                VideoCrud.update_status(video.id, VideoStatus.skipped_due_to_empty_subtitle, reason="No subtitle")
                logger.warning(f"[{video.id} | {video.host} | {video.original_id}] no subtitle, skipping")
                continue

            logger.info(f"[{video.id} | {video.host} | {video.original_id}] vtt translation started")
            path = StorePath(video.host, video.original_id)

            try:
                vtt_content = path.vtt.read_text()
                path.translated_vtts.mkdir(exist_ok=True)

                with ThreadPoolExecutor(max_workers=len(Language)) as executor:
                    futures = [
                        executor.submit(translate_and_save, lang, vtt_content, path, video)
                        for lang in Language
                    ]
                    for future in futures:
                        future.result()

                VideoCrud.update_status(video.id, VideoStatus.vtt_translated)
                logger.info(f"[{video.id} | {video.host} | {video.original_id}] all vtt translated")
            except Exception as e:
                reason = str(e)[:DB_ERROR_LOG_LENGTH]
                VideoCrud.update_status(video.id, VideoStatus.failed_vtt_translated, reason)
                exception_count += 1
                if exception_count >= 3:
                    raise e
                traceback.print_exc()


if __name__ == '__main__':
    init_logging("translate_vtt")
    host = sys.argv[1] if len(sys.argv) > 1 else ""
    process_subtitled_videos(10, host)
    logger.info("All vtts translated")
