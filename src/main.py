import argparse
from loguru import logger

from src.service.s1_fetch import fetch_and_save_videos
from src.service.s2_download import download_videos
from src.service.s3_convert import convert_videos
from src.service.s4_subtitle import generate_subtitle
from src.service.s5_translate_vtt import process_subtitled_videos
from src.service.s6_translate_meta import translate_meta_infos
from src.service.s7_upload import upload_videos
from src.service.s8_cleanup import clean_files
from src.utils.log_utils import init_logging

# Map of runner names to their corresponding functions and required arguments
RUNNERS = {
    "s1_fetch": (fetch_and_save_videos, {"max_pages": True, "batch_size": True, "host": False}),
    "s2_download": (download_videos, {"batch_size": True, "host": True}),
    "s3_convert": (convert_videos, {"batch_size": True, "host": True}),
    "s4_subtitle": (generate_subtitle, {"batch_size": True, "host": True}),
    "s5_translate_vtt": (process_subtitled_videos, {"batch_size": True, "host": True}),
    "s6_translate_meta": (translate_meta_infos, {"batch_size": True, "host": True}),
    "s7_upload": (upload_videos, {"batch_size": True, "host": True}),
    "s8_cleanup": (clean_files, {"batch_size": True, "host": True}),
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Video processing pipeline runner")
    parser.add_argument("--runner", type=str, help="Pipeline stage to run (e.g., s1_fetch, s2_download)", required=True)
    parser.add_argument("--batch-size", type=int, help="Number of items to process in each batch", default=3)
    parser.add_argument("--host", type=str, help="Target host to process", default="")
    parser.add_argument("--max-pages", type=int, help="Maximum number of pages to crawl (for s1_fetch)", default=2)

    args = parser.parse_args()
    init_logging(args.runner)
    logger.info(f"Starting runner: {args.runner} with args: {args}")

    if args.runner not in RUNNERS:
        logger.error(f"Invalid runner: {args.runner}")
        exit(1)

    runner_func, required_args = RUNNERS[args.runner]
    kwargs = {}
    
    if required_args.get("batch_size"):
        kwargs["batch_size"] = args.batch_size
    if required_args.get("host"):
        kwargs["host"] = args.host
    if required_args.get("max_pages"):
        kwargs["max_pages"] = args.max_pages

    runner_func(**kwargs)
