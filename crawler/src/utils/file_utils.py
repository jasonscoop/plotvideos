import json
import shutil
from pathlib import Path
from typing import Union

from loguru import logger

from core.models import Video


def save_json(path: Union[str, Path], json_data: dict | list):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False))


def _safe_video_store_parent(path: Path, video_id: int) -> bool:
    from core.path_layout import store_prefix
    from core.workdirs import VIDEOS_DIR

    try:
        resolved = path.resolve()
        base = VIDEOS_DIR.resolve()
        if not resolved.is_relative_to(base):
            return False
        rel = resolved.relative_to(base)
        parts = rel.parts
        if len(parts) != 2:
            return False
        shard, vid = parts[0], parts[1]
        if len(shard) != 2 or not shard.isdigit():
            return False
        if not vid.isdigit() or int(vid) != int(video_id):
            return False
        expected = store_prefix(video_id)
        if f"{shard}/{vid}" != expected:
            return False
        return True
    except (ValueError, OSError):
        return False


def rm_video(video: Video) -> bool:
    from core.schemas import StorePath

    parent = StorePath(video.id).parent
    if not parent.exists():
        return True
    if not _safe_video_store_parent(parent, video.id):
        logger.warning(
            "rm_video: refused or could not verify store dir for video id={} path={}",
            video.id,
            parent,
        )
        return False
    try:
        shutil.rmtree(str(parent), ignore_errors=False)
    except OSError as e:
        logger.warning("rm_video: rmtree failed id={} path={}: {}", video.id, parent, e)
        raise
    return not parent.exists()


def rm_by_id(video_id: int) -> bool:
    from core.schemas import StorePath

    parent = StorePath(video_id).parent
    if not parent.exists():
        return True
    if not _safe_video_store_parent(parent, video_id):
        logger.warning(
            "rm_by_id: refused or could not verify store dir for video id={} path={}",
            video_id,
            parent,
        )
        return False
    shutil.rmtree(str(parent), ignore_errors=True)
    return not parent.exists()
