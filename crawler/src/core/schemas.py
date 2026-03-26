from pathlib import Path

from core.path_layout import store_prefix


class StorePath:
    def __init__(self, video_id: int):
        from core.workdirs import VIDEOS_DIR

        self.prefix: str = self.build_prefix(video_id)
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
    def build_prefix(cls, video_id: int) -> str:
        return store_prefix(video_id)
