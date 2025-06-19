import json
import re
import shutil
from pathlib import Path
from typing import Union

import boto3
from loguru import logger

from src.lib.config import S3_BUCKET_NAME, S3_SECRET_KEY, S3_REGION, S3_ACCESS_KEY
from src.lib.models import Video

s3_client = boto3.client(
    "s3",
    aws_access_key_id=S3_ACCESS_KEY,
    aws_secret_access_key=S3_SECRET_KEY,
    region_name=S3_REGION,
)


async def upload_to_s3(self, file_bytes: bytes, file_path: str):
    self.s3_client.put_object(Bucket=S3_BUCKET_NAME, Key=file_path, Body=file_bytes)


def upload_dir_to_s3(local_dir: Path, s3_prefix=''):
    for file_path in local_dir.rglob('*'):
        if file_path.is_file() and file_path.name != '.DS_Store':
            relative_path = file_path.relative_to(local_dir)
            s3_key = str(Path(s3_prefix) / relative_path).replace("\\", "/")  # ensure S3 key uses forward slashes
            s3_client.upload_file(str(file_path), S3_BUCKET_NAME, s3_key)


def save_json(path: Union[str, Path], json_data: dict):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(json_data, indent=2, ensure_ascii=False))


def is_path_match(path: str) -> bool:
    return re.match(r'.*/works/videos/\w{2}/[a-zA-Z]{2}/\w+$', path) is not None


def rm_video(video: Video):
    if video.path.parent.exists() and is_path_match(video.path.parent.as_posix()):
        shutil.rmtree(str(video.path.parent), ignore_errors=False)
    else:
        logger.warning(f"Video {video.path} does not exist")
