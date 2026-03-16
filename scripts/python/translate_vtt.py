from botocore.exceptions import ClientError
from loguru import logger

from crawler.crud.video_crud import VideoCrud
from crawler.lib.config import S3_BUCKET_NAME
from crawler.lib.enums import VideoStatus
from crawler.lib.languages import Language
from crawler.lib.models import Video
from crawler.service.s5_translate_vtt import translate_and_save
from crawler.service.s7_upload import bunny_client
from crawler.utils.file_utils import upload_dir_to_s3, s3_client
from crawler.utils.log_utils import init_logging

BATCH_SIZE = 10
MAX_ID = 27555
LAST_ID = 5744


def download_vtt_from_s3(video: Video):
    vtt_path = video.store_path.vtt
    vtt_path.parent.mkdir(parents=True, exist_ok=True)
    s3_client.download_file(S3_BUCKET_NAME, video.store_path.vtt_s3_key, str(vtt_path))


def translate_video(video: Video, languages: list[Language]):
    try:
        download_vtt_from_s3(video)
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            logger.error(f"Object not found. {str(e)}")
            return

    if not video.store_path.vtt.exists():
        logger.warning(f"[{video.id}] VTT file doesn't exist, skipping translation")
        return

    video.store_path.translated_vtts.mkdir(exist_ok=True)
    vtt_content = video.store_path.vtt.read_text()
    for lang in languages:
        translate_and_save(lang, vtt_content, video)
    logger.info(f"[{video.id}] translated.")

    guid = video.bunny_video_id
    for lang in languages:
        vtt_file = video.store_path.translated_vtts / f"{lang.code}.vtt"
        if vtt_file.exists() and guid:
            bunny_client.upload_subtitle(guid, vtt_file, lang)

    # Upload to S3
    upload_dir_to_s3(
        video.store_path.translated_vtts, video.store_path.translated_s3_key
    )
    VideoCrud.update({"id": video.id, "temp_status": 2})
    logger.info(f"[{video.id}] uploaded.")
    return video.id


def main():
    last_id = LAST_ID
    languages = Language.get_all()
    while True:
        # Get videos that have VTT files but may not have translations
        videos = VideoCrud.batch_get(
            last_id,
            BATCH_SIZE,
            status=[VideoStatus.uploaded, VideoStatus.published],
            temp_status=1,
        )
        videos = [v for v in videos if v.id <= MAX_ID]
        if not videos:
            logger.info("All translation done!")
            break

        last_id = videos[-1].id
        for video in videos:
            translate_video(video, languages)


if __name__ == "__main__":
    # 1. look at the supabase for videos with VTT files
    # 2. translate subtitles for all languages using @s5_translate_vtt.py
    # 3. upload translated subtitles to bunny.net and S3 like @s7_upload.py
    # note: 1. using multiple processes to speed up the process
    # note: 2. save the last_id in a file and load it when the script is run again
    init_logging("translate_vtt")
    main()
