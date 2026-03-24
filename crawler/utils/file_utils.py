import json
import re
import shutil
from pathlib import Path
from typing import Union


from crawler.core.models import Video


def save_json(path: Union[str, Path], json_data: dict | list):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False))


def is_path_match(path: str) -> bool:
    return re.match(r".*/works/videos/[a-z]{2}/[a-z]{2}/\w+$", path) is not None


def rm_video(video: Video):
    if video.store_path.parent.exists() and is_path_match(
        video.store_path.parent.as_posix()
    ):
        shutil.rmtree(str(video.store_path.parent), ignore_errors=False)
