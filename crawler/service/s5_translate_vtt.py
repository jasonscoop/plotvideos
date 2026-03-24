import time
import traceback

import webvtt
from loguru import logger

from crawler.crud.video_crud import VideoCrud
from crawler.core.config import SUBTITLE_TOKEN_RATIO_THRESHOLD, S5_TRANSLATE_VTT_BATCH_SIZE
from crawler.core.enums import VideoStatus
from crawler.core.languages import Language
from crawler.utils.signal_utils import setup_graceful_shutdown, should_stop
from crawler.utils.translate_utils import translate_list


def translate_vtt(vtt_content: str, lang) -> str:
    vtt = webvtt.from_string(vtt_content)
    texts = [c.text for c in vtt]
    translated_texts = translate_list(texts, lang)

    if len(translated_texts) != len(vtt.captions):
        raise ValueError(
            f"Translation count mismatch: expected {len(vtt.captions)}, got {len(translated_texts)}"
        )

    for i, t in enumerate(translated_texts):
        vtt.captions[i].text = t

    return vtt.content


def translate_and_save(lang, vtt_content, video):
    translated_vtt = translate_vtt(vtt_content, lang)
    translated_file = video.store_path.translated_vtts / f"{lang.code}.vtt"
    translated_file.write_text(translated_vtt)
    logger.info(
        f"[{video.id} | {video.host} | {video.original_id}] vtt translated '{lang.code}'"
    )


def process_subtitled_videos(host: str = ""):
    setup_graceful_shutdown()
    last_id = None
    languages = Language.get_all()

    while not should_stop():
        videos = VideoCrud.batch_get(
            last_id, S5_TRANSLATE_VTT_BATCH_SIZE, VideoStatus.subtitled, host
        )
        if not videos:
            logger.info("All vtt translated, sleeping for 5 minutes")
            time.sleep(5 * 60)
            last_id = None
            continue

        last_id = videos[-1].id
        exception_count = 0

        for video in videos:
            if len(video.subtitle_content.strip()) == 0:
                reason = VideoCrud.record_failure(
                    video.id,
                    VideoStatus.subtitled.log("Subtitle content is empty"),
                )
                logger.warning(
                    f"[{video.id} | {video.host} | {video.original_id}] {reason}"
                )
                continue

            if video.word_density < SUBTITLE_TOKEN_RATIO_THRESHOLD:
                reason = VideoCrud.record_failure(
                    video.id,
                    VideoStatus.subtitled.log("Subtitle content is too short"),
                )
                logger.warning(
                    f"[{video.id} | {video.host} | {video.original_id}] {reason}"
                )
                continue

            if not video.store_path.vtt.exists():
                reason = VideoCrud.record_failure(
                    video.id,
                    VideoStatus.subtitled.log("Subtitle file isn't exist"),
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

                for lang in languages:
                    translate_and_save(lang, vtt_content, video)

                VideoCrud.update_status(video.id, VideoStatus.vtt_translated)
                logger.info(
                    f"[{video.id} | {video.host} | {video.original_id}] all vtt translated"
                )
            except Exception as e:
                reason = VideoCrud.record_failure(
                    video.id, VideoStatus.vtt_translated.log(e)
                )
                logger.error(f"[{video.id} | {video.original_id}] {reason}")
                exception_count += 1
                if exception_count >= 3:
                    raise e
                traceback.print_exc()
