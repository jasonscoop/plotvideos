import multiprocessing
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed

multiprocessing.set_start_method("spawn", force=True)

from loguru import logger

from src.crud.video_crud import VideoCrud
from src.lib.enums import VideoStatus
from src.lib.models import Video
from src.utils.file_utils import s3_client, S3_BUCKET_NAME
from src.utils.log_utils import init_logging
from src.utils.string_utils import get_tokens
from src.utils.whisper_utils import whisper_transcribe

BATCH_SIZE = 5
MAX_ID = 27555


def download_wav_from_s3(video: Video):
    wav_path = video.path.audio
    s3_key = f"{video.path.prefix}/audio.wav"
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    s3_client.download_file(S3_BUCKET_NAME, s3_key, str(wav_path))


def upload_vtt_to_s3(video: Video):
    s3_key = f"{video.path.prefix}/subtitle.vtt"
    s3_client.upload_file(str(video.path.vtt), S3_BUCKET_NAME, s3_key)


def transcribe_video(video: Video):
    t0 = time.time()
    logger.info(f"[{video.id}] downloading...")
    download_wav_from_s3(video)
    logger.info(f"[{video.id}] downloaded in {time.time() - t0:.1f}s")

    vtt_content, sub_text = whisper_transcribe(video.path)
    video.path.vtt.write_text(vtt_content)
    logger.info(f"[{video.id}] generated in {time.time() - t0:.1f}s.")
    t1 = time.time()

    upload_vtt_to_s3(video)
    logger.info(f"[{video.id}] uploaded in {time.time() - t1:.1f}s.")
    t2 = time.time()

    tokens = get_tokens(sub_text)
    subtitle_duration_ratio = round(tokens / video.duration, 2) if video.duration else 0
    VideoCrud.update({
        "id": video.id,
        "subtitle_content": sub_text,
        "subtitle_tokens": tokens,
        "subtitle_duration_ratio": subtitle_duration_ratio,
        "temp_status": 1
    })

    # remove the wav file and vtt
    video.path.audio.unlink(missing_ok=True)
    video.path.vtt.unlink(missing_ok=True)

    logger.info(f"[{video.id}] db updated in {time.time() - t2:.2f}s.")


def main():
    last_id = 0
    while True:
        videos = VideoCrud.batch_get(last_id, BATCH_SIZE, status=[VideoStatus.uploaded, VideoStatus.published],
                                     temp_status=0)
        videos = [v for v in videos if v.id <= MAX_ID]
        if not videos:
            logger.info("All transcription done!")
            break

        last_id = videos[-1].id
        with ProcessPoolExecutor(max_workers=BATCH_SIZE) as executor:
            futures = {executor.submit(transcribe_video, v): v for v in videos}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error transcribing video: {e}")
                    traceback.print_exc()
                    raise e


if __name__ == "__main__":
    # 1. look at the supabase for the id <= 27555
    # 2. get the wav file from s3 in @file_utils.py
    # 3. extract the subtitle with whisper in @whisper_utils.py
    # 4. save subtitle content to database
    # note: 1. using multiple processes to speed up the process
    # note: 2. save the last_id in a file and load it when the script is run again
    init_logging("retranscribe")
    main()
