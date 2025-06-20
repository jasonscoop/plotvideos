import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.config import WORKS_DIR
from src.lib.enums import VideoStatus
from src.lib.models import Video
from src.utils.file_utils import s3_client, S3_BUCKET_NAME
from src.utils.log_utils import init_logging
from src.utils.string_utils import get_tokens
from src.utils.whisper_utils import whisper_transcribe

LAST_ID_FILE = WORKS_DIR / "retranscribe_last_id.txt"
BATCH_SIZE = 5
MAX_ID = 27555


def load_last_id():
    if LAST_ID_FILE.exists():
        return int(LAST_ID_FILE.read_text().strip())
    return 0


def save_last_id(last_id):
    LAST_ID_FILE.write_text(str(last_id))


def download_wav_from_s3(video: Video):
    wav_path = video.path.audio
    s3_key = f"{video.path.prefix}/audio.wav"
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"[{video.id}] '{s3_key}' Downloading from S3")
    s3_client.download_file(S3_BUCKET_NAME, s3_key, str(wav_path))


def transcribe_video(video: Video):
    """Transcribe video audio and save subtitle content to database"""
    download_wav_from_s3(video)
    sub, vtt_text = whisper_transcribe(video.path)
    logger.info(f"[{video.id}] subtitle generated.")

    tokens = get_tokens(vtt_text)
    subtitle_duration_ratio = round(tokens / video.duration, 2) if video.duration else 0

    VideoCrud.update({
        "id": video.id,
        "subtitle_content": vtt_text,
        "subtitle_tokens": tokens,
        "subtitle_duration_ratio": subtitle_duration_ratio,
    })

    logger.info(f"[{video.id}] subtitle content saved to database.")
    return video.id


def main():
    last_id = load_last_id()
    while True:
        videos = VideoCrud.batch_get(last_id, BATCH_SIZE, status=[VideoStatus.uploaded, VideoStatus.published])
        videos = [v for v in videos if v.id <= MAX_ID]
        if not videos:
            logger.info("All transcription done!")
            break

        with ProcessPoolExecutor(max_workers=BATCH_SIZE) as executor:
            futures = {executor.submit(transcribe_video, v): v for v in videos}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error transcribing video: {e}")
                    traceback.print_exc()
                    raise e

        last_id = videos[-1].id
        save_last_id(last_id)


if __name__ == "__main__":
    # 1. look at the supabase for the id <= 27555
    # 2. get the wav file from s3 in @file_utils.py
    # 3. extract the subtitle with whisper in @whisper_utils.py
    # 4. save subtitle content to database
    # note: 1. using multiple processes to speed up the process
    # note: 2. save the last_id in a file and load it when the script is run again
    init_logging("retranscribe")
    main()
