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
from src.service.s5_translate_vtt import translate_and_save
from src.utils.bunny_utils import BunnyStreamClient
from src.utils.file_utils import upload_dir_to_s3
from src.utils.log_utils import init_logging

LAST_ID_FILE = WORKS_DIR / "translate_vtt_last_id.txt"
BATCH_SIZE = 4
MAX_ID = 27555

bunny_client = BunnyStreamClient(BUNNY_API_KEY, BUNNY_LIBRARY_ID)


def load_last_id():
    if LAST_ID_FILE.exists():
        return int(LAST_ID_FILE.read_text().strip())
    return 0


def save_last_id(last_id):
    LAST_ID_FILE.write_text(str(last_id))


def translate_video(video: Video, languages: list[Language]):
    """Translate video subtitles and upload to bunny.net and S3"""
    # Check if VTT file exists
    if not video.path.vtt.exists():
        logger.warning(f"[{video.id}] VTT file doesn't exist, skipping translation")
        return video.id
    
    # Create translated_vtts directory
    video.path.translated_vtts.mkdir(exist_ok=True)
    
    # Read VTT content
    vtt_content = video.path.vtt.read_text()
    
    # Translate for each language
    for lang in languages:
        translate_and_save(lang, vtt_content, video)

    logger.info(f"[{video.id}] subtitle translated.")

    # Upload to bunny.net
    guid = video.bunny_video_id
    for lang in languages:
        vtt_file = video.path.translated_vtts / f"{lang.code}.vtt"
        if vtt_file.exists() and guid:
            bunny_client.upload_subtitle(guid, vtt_file, lang)
    
    # Upload to S3
    upload_dir_to_s3(video.path.parent, video.path.prefix)

    logger.info(f"[{video.id}] subtitles uploaded to bunny.net and S3.")
    return video.id


def main():
    last_id = load_last_id()
    languages = LanguageCrud.get_all()
    while True:
        # Get videos that have VTT files but may not have translations
        videos = VideoCrud.batch_get(last_id, BATCH_SIZE, status=[VideoStatus.uploaded, VideoStatus.published])
        videos = [v for v in videos if v.id <= MAX_ID and v.path.vtt.exists()]
        if not videos:
            logger.info("All translation done!")
            break

        with ProcessPoolExecutor(max_workers=BATCH_SIZE) as executor:
            futures = {executor.submit(translate_video, v, languages): v for v in videos}
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Error translating video: {e}")
                    traceback.print_exc()
                    raise e

        last_id = videos[-1].id
        save_last_id(last_id)
        time.sleep(1)


if __name__ == "__main__":
    # 1. look at the supabase for videos with VTT files
    # 2. translate subtitles for all languages using @s5_translate_vtt.py
    # 3. upload translated subtitles to bunny.net and S3 like @s7_upload.py
    # note: 1. using multiple processes to speed up the process
    # note: 2. save the last_id in a file and load it when the script is run again
    init_logging("translate_vtt")
    main()
