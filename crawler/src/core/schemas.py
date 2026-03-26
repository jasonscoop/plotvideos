from pathlib import Path

from core.consts import VIDEOS_DIR


class StorePath:
    """Local + B2 layout: ``{id % 100 :02d}/{id}/…``.

    Shard is ``id mod 100`` (00–99) so buckets stay balanced; the full ``id`` in the
    next segment keeps paths unique (e.g. ``05/5/…``, ``05/105/…``, ``23/123/…``).
    """

    def __init__(self, video_id: int):
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
        if not video_id:
            raise ValueError("video id is required")
        vid = int(video_id)
        shard = f"{vid % 100:02d}"
        return f"{shard}/{vid}"
