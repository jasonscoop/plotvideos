import asyncio
import sys
import traceback
from concurrent.futures import ThreadPoolExecutor

import webvtt
from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.config import SUBTITLE_TOKEN_RATIO_THRESHOLD
from src.lib.enums import Language, VideoStatus
from src.utils.file_utils import rm_video
from src.utils.llm_utils import llm_translate_vtt
from src.utils.log_utils import init_logging
from src.utils.translate_utils import translate_texts
from src.utils.vtt_utils import is_valid_vtt


def google_translate_vtt(vtt_content, lang) -> str:
    vtt = webvtt.from_string(vtt_content)
    texts = [c.text for c in vtt]
    translated_texts = translate_texts(texts, lang)

    for i, t in enumerate(translated_texts):
        vtt.captions[i].text = t

    return vtt.content


def translate_and_save(lang, vtt_content, video):
    translated_vtt = llm_translate_vtt(vtt_content, lang)
    if not is_valid_vtt(translated_vtt):
        logger.warning(
            f"[{video.id} | {video.host} | {video.original_id}] Translated with llm failed, using google translator '{lang.short_code}'")
        translated_vtt = google_translate_vtt(vtt_content, lang)

    translated_file = video.path.translated_vtts / f"{lang.short_code}.vtt"
    translated_file.write_text(translated_vtt)
    logger.info(f"[{video.id} | {video.host} | {video.original_id}] vtt translated '{lang.short_code}'")


def process_subtitled_videos(batch_size: int = 10, host: str = ""):
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.subtitled, host)
        if not videos:
            break

        last_id = videos[-1].id

        for video in videos:
            if len(video.subtitle_content.strip()) == 0:
                reason = VideoCrud.update_status(video.id, VideoStatus.failed,
                                                 VideoStatus.subtitled.log("Subtitle content is empty"))
                logger.warning(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
                asyncio.run(rm_video(video))
                continue

            if video.subtitle_duration_ratio < SUBTITLE_TOKEN_RATIO_THRESHOLD:
                reason = VideoCrud.update_status(video.id, VideoStatus.failed,
                                                 reason=VideoStatus.subtitled.log("Subtitle content is too short"))
                logger.warning(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
                asyncio.run(rm_video(video))
                continue

            logger.info(f"[{video.id} | {video.host} | {video.original_id}] vtt translation started")

            try:
                vtt_content = video.path.vtt.read_text()
                video.path.translated_vtts.mkdir(exist_ok=True)

                with ThreadPoolExecutor(max_workers=len(Language)) as executor:
                    futures = [
                        executor.submit(translate_and_save, lang, vtt_content, video)
                        for lang in Language
                    ]
                    for future in futures:
                        future.result()

                VideoCrud.update_status(video.id, VideoStatus.vtt_translated)
                logger.info(f"[{video.id} | {video.host} | {video.original_id}] all vtt translated")
            except Exception as e:
                reason = VideoCrud.update_status(video.id, VideoStatus.failed, VideoStatus.vtt_translated.log(e))
                logger.error(f"[{video.id} | {video.original_id}] {reason}")
                exception_count += 1
                if exception_count >= 3:
                    raise e
                traceback.print_exc()
                asyncio.run(rm_video(video))


if __name__ == '__main__':
    init_logging("translate_vtt")

    batch_size = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    host = sys.argv[2] if len(sys.argv) > 2 else ""

    process_subtitled_videos(batch_size, host)
    logger.info("All vtts translated")
