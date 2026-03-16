from pathlib import Path

from sqlalchemy.sql.coercions import cls

from crawler.core.config import VIDEOS_DIR
from crawler.core.consts import WEBSITES


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

        self.hls_s3_prefix = self.prefix + "/hls"
        self.hls_dir: Path = VIDEOS_DIR / self.hls_s3_prefix
        self.hls_master_s3_key = self.hls_s3_prefix + "/master.m3u8"
        self.hls_master: Path = VIDEOS_DIR / self.hls_master_s3_key

    @classmethod
    def build_prefix(cls, host: str, original_id: str):
        if host not in WEBSITES:
            raise ValueError(f"❌ Can not find website from {host}")

        if not original_id:
            raise ValueError(f"❌ Original id is required")

        return f"{WEBSITES[host][0]}/{original_id[0:2]}/{original_id}"
