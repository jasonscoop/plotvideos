import re
import traceback
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from loguru import logger

from src.lib.consts import SubtitleType
from src.utils.azure_subtitle_utils import generate_subtitle
from src.utils.log_utils import init_logging


if __name__ == '__main__':
    init_logging("subtitles")
    dir_path = "/Users/garymeng/code/more/wuse/works/videos"
    files = []
    for filename in os.listdir(dir_path):
        full_path = os.path.join(dir_path, filename)
        if os.path.isfile(full_path) and (full_path.endswith(".mp4") or full_path.endswith(".webm")):
            files.append((re.sub(r'\[\w+]', '', filename), full_path))
            logger.info(re.sub(r'\[\w+]', '', filename))

    with ThreadPoolExecutor(max_workers=len(files)) as executor:
        futures = []
        for f in files:
            futures.append(executor.submit(generate_subtitle, f[0], Path(f[1]), SubtitleType.vtt))

        for future in as_completed(futures):
            try:
                future.result()  # This raises any exceptions from the thread
            except Exception as e:
                traceback.print_exc()
