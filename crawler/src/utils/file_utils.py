import json
import re
import shutil
from pathlib import Path
from typing import Union


from core.models import Video


def save_json(path: Union[str, Path], json_data: dict | list):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False))


def is_path_match(path: str) -> bool:
    # ``works/videos/{shard}/{id}`` (e.g. 05/5, 12/1234)
    return re.match(r".*/works/videos/\d{2}/\d+$", path) is not None


def rm_video(video: Video) -> bool:
    parent = video.store_path.parent
    if not parent.exists():
        return True
    if is_path_match(parent.as_posix()):
        shutil.rmtree(str(parent), ignore_errors=False)
        return not parent.exists()
    return False


def rm_by_id(video_id: int) -> bool:
    from core.schemas import StorePath

    parent = StorePath(video_id).parent
    if not parent.exists():
        return True
    if is_path_match(parent.as_posix()):
        shutil.rmtree(str(parent), ignore_errors=True)
        return not parent.exists()
    return False
