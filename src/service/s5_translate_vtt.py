import time
import traceback
from concurrent.futures import ThreadPoolExecutor

import webvtt
from loguru import logger
from requests import HTTPError

from src.crud.language_crud import LanguageCrud
from src.crud.video_crud import VideoCrud
from src.lib.config import SUBTITLE_TOKEN_RATIO_THRESHOLD, S5_TRANSLATE_VTT_BATCH_SIZE
from src.lib.enums import VideoStatus
from src.utils.file_utils import rm_video
from src.utils.llm_utils import llm_translate_vtt
from src.utils.translate_utils import translate_texts2, translate_texts1


def google_translate_vtt(vtt_content, lang, video) -> str:
    vtt = webvtt.from_string(vtt_content)
    texts = [c.text for c in vtt]
    try:
        translated_texts = translate_texts1(texts, lang)
        logger.error(
            f"[{video.id} | {video.host} | {video.original_id}] translated with translator1"
        )
    except HTTPError as e:
        translated_texts = translate_texts2(texts, lang)
        logger.error(
            f"[{video.id} | {video.host} | {video.original_id}] translated with translator2 (fallback)"
        )

    for i, t in enumerate(translated_texts):
        vtt.captions[i].text = t

    return vtt.content


def translate_and_save(lang, vtt_content, video):
    translated_vtt = llm_translate_vtt(vtt_content, lang)
    if not translated_vtt:
        logger.warning(
            f"[{video.id} | {video.host} | {video.original_id}] Translated with llm failed, using google translator '{lang.code}'"
        )
        translated_vtt = google_translate_vtt(vtt_content, lang, video)

    translated_file = video.store_path.translated_vtts / f"{lang.code}.vtt"
    translated_file.write_text(translated_vtt)
    logger.info(
        f"[{video.id} | {video.host} | {video.original_id}] vtt translated '{lang.code}'"
    )


def process_subtitled_videos(host: str = ""):
    last_id = None
    exception_count = 0
    languages = LanguageCrud.get_all()

    while True:
        videos = VideoCrud.batch_get(
            last_id, S5_TRANSLATE_VTT_BATCH_SIZE, VideoStatus.subtitled, host
        )
        if not videos:
            logger.info("All vtt translated, sleeping for 5 minutes")
            time.sleep(5 * 60)
            last_id = None
            languages = LanguageCrud.get_all()
            continue

        last_id = videos[-1].id

        for video in videos:
            if len(video.subtitle_content.strip()) == 0:
                reason = VideoCrud.update_status(
                    video.id,
                    VideoStatus.failed,
                    VideoStatus.subtitled.log("Subtitle content is empty"),
                )
                logger.warning(
                    f"[{video.id} | {video.host} | {video.original_id}] {reason}"
                )
                continue

            if video.word_density < SUBTITLE_TOKEN_RATIO_THRESHOLD:
                reason = VideoCrud.update_status(
                    video.id,
                    VideoStatus.failed,
                    reason=VideoStatus.subtitled.log("Subtitle content is too short"),
                )
                logger.warning(
                    f"[{video.id} | {video.host} | {video.original_id}] {reason}"
                )
                continue

            if not video.store_path.vtt.exists():
                reason = VideoCrud.update_status(
                    video.id,
                    VideoStatus.failed,
                    reason=VideoStatus.subtitled.log("Subtitle file isn't exist"),
                )
                logger.warning(
                    f"[{video.id} | {video.host} | {video.original_id}] {reason}"
                )
                continue

            logger.info(
                f"[{video.id} | {video.host} | {video.original_id}] vtt translation started"
            )

            try:
                vtt_content = video.store_path.vtt.read_text()
                video.store_path.translated_vtts.mkdir(exist_ok=True)

                with ThreadPoolExecutor(max_workers=len(languages)) as executor:
                    futures = [
                        executor.submit(translate_and_save, lang, vtt_content, video)
                        for lang in languages
                    ]
                    for future in futures:
                        future.result()

                VideoCrud.update_status(video.id, VideoStatus.vtt_translated)
                logger.info(
                    f"[{video.id} | {video.host} | {video.original_id}] all vtt translated"
                )
            except Exception as e:
                reason = VideoCrud.update_status(
                    video.id, VideoStatus.failed, VideoStatus.vtt_translated.log(e)
                )
                logger.error(f"[{video.id} | {video.original_id}] {reason}")
                exception_count += 1
                if exception_count >= 3:
                    raise e
                traceback.print_exc()
