import time
import traceback
from pathlib import Path

import requests
from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.config import S4_SUBTITLE_BATCH_SIZE, AUDIO2VTT_ENDPOINT, AUDIO2VTT_API_KEY
from src.lib.models import VideoStatus
from src.utils.file_utils import rm_video
from src.utils.string_utils import get_tokens
from src.utils.vtt_utils import get_vtt_text


def audio2text(audio_path: Path, language: str = "en") -> str:
    headers = {
        "accept": "application/json",
        "X-API-Key": AUDIO2VTT_API_KEY,
    }
    files = {
        "file": (audio_path.name, open(audio_path, "rb")),
        "language": (None, language),
    }
    response = requests.post(
        AUDIO2VTT_ENDPOINT,
        headers=headers,
        files=files,
    )
    return response.text


def subtitle_video(video):
    try:
        vtt_content = audio2text(video.path)
        video.path.vtt.write_text(vtt_content)

        subtitle_content = get_vtt_text(vtt_content)
        tokens = get_tokens(get_vtt_text(vtt_content))

        VideoCrud.update(
            {
                "id": video.id,
                "subtitle_content": subtitle_content,
                "subtitle_tokens": tokens,
                "subtitle_duration_ratio": round(tokens / video.duration, 2),
                "status": VideoStatus.subtitled,
                "failed_reason": "",
            }
        )
        logger.info(
            f"[{video.id} | {video.host} | {video.original_id}] subtitle generated"
        )
        return None
    except Exception as e:
        reason = VideoCrud.update_status(
            video.id, VideoStatus.failed, VideoStatus.subtitled.log(e)
        )
        logger.info(f"[{video.id} | {video.host} | {video.original_id}] {reason}")
        traceback.print_exc()
        rm_video(video)
        return e


def subtitle_videos(host: str = ""):
    last_id = 0

    while True:
        videos = VideoCrud.batch_get(
            last_id, S4_SUBTITLE_BATCH_SIZE, VideoStatus.converted, host
        )
        if not videos:
            logger.info("All subtitled, sleeping for 5 minutes")
            time.sleep(5 * 60)
            last_id = 0
            continue

        last_id = videos[-1].id
        for video in videos:
            subtitle_video(video)
