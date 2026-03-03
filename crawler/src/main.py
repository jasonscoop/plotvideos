import argparse

from loguru import logger

from src.service.s1_fetch import fetch_and_save_videos
from src.service.s2_download import download_videos
from src.service.s3_convert import convert_videos
from src.service.s4_subtitle import subtitle_videos
from src.service.s5_translate_vtt import process_subtitled_videos
from src.service.s6_translate_meta import translate_meta_infos
from src.service.s7_upload import upload_videos
from src.service.s8_cleanup import clean_files
from src.utils.log_utils import init_logging

RUNNERS = {
    "s1_fetch": fetch_and_save_videos,
    "s2_download": download_videos,
    "s3_convert": convert_videos,
    "s4_subtitle": subtitle_videos,
    "s5_translate_vtt": process_subtitled_videos,
    "s6_translate_meta": translate_meta_infos,
    "s7_upload": upload_videos,
    "s8_cleanup": clean_files,
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Video processing pipeline runner")
    parser.add_argument("--runner", type=str, help="Pipeline stage to run (e.g., s1_fetch, s2_download)", required=True)
    parser.add_argument("--host", type=str, help="Target host to process", default="")

    args = parser.parse_args()
    init_logging(args.runner)
    logger.info(f"Starting runner: {args.runner} with args: {args}")

    if args.runner not in RUNNERS:
        logger.error(f"Invalid runner: {args.runner}")
        exit(1)

    runner_func = RUNNERS[args.runner]
    runner_func(host=args.host)
