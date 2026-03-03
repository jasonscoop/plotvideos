from pathlib import Path

from sqlalchemy.sql.coercions import cls

from crawler.lib.config import VIDEOS_DIR
from crawler.lib.consts import WEBSITES


class StorePath:
    def __init__(self, host: str, original_id: str):
        self.prefix: str = self.build_prefix(host, original_id)
        self.parent: Path = VIDEOS_DIR / self.prefix

        self.video_s3_key = self.prefix + "/video.mp4"
        self.vtt_s3_key = self.prefix + "/subtitle.vtt"
        self.translated_s3_key = self.prefix + "/subtitles/"
        self.audio_s3_key = self.prefix + "/audio.wav"
        self.thumbnail_s3_key = self.prefix + "/thumbnail.webp"

        self.video: Path = VIDEOS_DIR / self.video_s3_key
        self.vtt: Path = VIDEOS_DIR / self.vtt_s3_key
        self.translated_vtts: Path = VIDEOS_DIR / self.translated_s3_key
        self.audio: Path = VIDEOS_DIR / self.audio_s3_key
        self.thumbnail: Path = VIDEOS_DIR / self.thumbnail_s3_key

        self.segments: Path = self.parent / "segments.json"

    @classmethod
    def build_prefix(cls, host: str, original_id: str):
        if host not in WEBSITES:
            raise ValueError(f"❌ Can not find website from {host}")

        if not original_id:
            raise ValueError(f"❌ Original id is required")

        return f"{WEBSITES[host][0]}/{original_id[0:2]}/{original_id}"
