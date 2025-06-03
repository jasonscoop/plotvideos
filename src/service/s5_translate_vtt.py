import traceback

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.consts import DB_ERROR_LOG_LENGTH
from src.lib.enums import VideoStatus, Language
from src.lib.schemas import StorePath
from src.utils.llm_utils import translate_vtt
from src.utils.log_utils import init_logging


def process_subtitled_videos(batch_size: int = 10):
    last_id = 0
    exception_count = 0

    while True:
        videos = VideoCrud.batch_get(last_id, batch_size, VideoStatus.meta_translated)
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

                for lang in Language:
                    translated_vtt = translate_vtt(vtt_content, lang)
                    translated_file = path.translated_vtts / f"{lang.short_code}.vtt"
                    translated_file.write_text(translated_vtt)

                VideoCrud.update_status(video.id, VideoStatus.vtt_translated)
                logger.info(f"[{video.id} | {video.host} | {video.original_id}] ")
            except Exception as e:
                reason = str(e)[:DB_ERROR_LOG_LENGTH]
                VideoCrud.update_status(video.id, VideoStatus.failed_vtt_translated, reason)
                exception_count += 1
                if exception_count >= 3:
                    raise e
                traceback.print_exc()


if __name__ == '__main__':
    init_logging("translate_vtt")
    process_subtitled_videos()
