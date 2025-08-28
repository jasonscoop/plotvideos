from pathlib import Path

from src.lib.config import VIDEOS_DIR
from src.lib.consts import WEBSITES


class StorePath:
    def __init__(self, host: str, original_id: str):
        self.prefix: str = (
            f"{WEBSITES[host]['short_name']}/{original_id[0:2]}/{original_id}"
        )

        self.video_s3_key = self.prefix + "/video.mp4"
        self.vtt_s3_key = self.prefix + "/subtitle.vtt"
        self.translated_s3_key = self.prefix + "/subtitles/"
        self.audio_s3_key = self.prefix + "/audio.wav"

        self.video: Path = VIDEOS_DIR / self.video_s3_key
        self.vtt: Path = VIDEOS_DIR / self.vtt_s3_key
        self.translated_vtts: Path = VIDEOS_DIR / self.translated_s3_key
        self.audio: Path = VIDEOS_DIR / self.audio_s3_key

        self.segments: Path = VIDEOS_DIR / self.prefix / "segments.json"
