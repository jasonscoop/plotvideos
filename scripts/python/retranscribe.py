import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed

from loguru import logger

from src.crud.language_crud import LanguageCrud
from src.crud.video_crud import VideoCrud
from src.lib.config import BUNNY_API_KEY, BUNNY_LIBRARY_ID, WORKS_DIR
from src.lib.enums import VideoStatus
from src.lib.models import Language
from src.lib.models import Video
from src.utils.bunny_utils import BunnyStreamClient
from src.utils.file_utils import s3_client, S3_BUCKET_NAME
from src.utils.file_utils import upload_dir_to_s3
from src.utils.llm_utils import llm_translate_vtt
from src.utils.log_utils import init_logging
from src.utils.vtt_utils import is_valid_vtt
from src.utils.whisper_utils import whisper_transcribe

LAST_ID_FILE = WORKS_DIR / "retranscribe_last_id.txt"
BATCH_SIZE = 4
MAX_ID = 27555

bunny_client = BunnyStreamClient(BUNNY_API_KEY, BUNNY_LIBRARY_ID)


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


def reprocess_video(video: Video, languages: list[Language]):
    download_wav_from_s3(video)
    vtt_content = whisper_transcribe(video.path)
    logger.info(f"[{video.id}] subtitle generated.")

    video.path.translated_vtts.mkdir(exist_ok=True)
    for lang in languages:
        translated_vtt = llm_translate_vtt(vtt_content, lang)
        if not is_valid_vtt(translated_vtt):
            continue
        translated_file = video.path.translated_vtts / f"{lang.code}.vtt"
        translated_file.write_text(translated_vtt)

    logger.info(f"[{video.id}] subtitle translated.")

    guid = video.bunny_video_id
    for lang in languages:
        vtt_file = video.path.translated_vtts / f"{lang.code}.vtt"
        if vtt_file.exists() and guid:
            bunny_client.upload_subtitle(guid, vtt_file, lang)
    upload_dir_to_s3(video.path.parent, video.path.prefix)

    logger.info(f"[{video.id}] subtitle uploaded.")
    return video.id


def main():
    last_id = load_last_id()
    languages = LanguageCrud.get_all()
    while True:
        videos = VideoCrud.batch_get(last_id, BATCH_SIZE, status=[VideoStatus.uploaded, VideoStatus.published])
        videos = [v for v in videos if v.id <= MAX_ID]
        if not videos:
            logger.info("All done!")
            break

        with ProcessPoolExecutor(max_workers=BATCH_SIZE) as executor:
            futures = {executor.submit(reprocess_video, v, languages): v for v in videos}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error processing video: {e}")
                    traceback.print_exc()
                    raise e

        last_id = videos[-1].id
        save_last_id(last_id)
        time.sleep(1)


if __name__ == "__main__":
    # 1. look at the supbase for the id <= 27555
    # 2. get the wav file from s3 in @file_utils.py
    # 3. extract the subtitle with whisper in @whisper_utils.py
    # 4. then re-translate the subtitle similar to @s5_translate_vtt.py
    # 5. then reupload the subtitles to s3 and bunny.net like @s7_upload.py
    # note: 1. using multiple processes to speed up the process
    # note: 2. save the last_id in a file and load it when the script is run again
    init_logging("retranscribe")
    main()
