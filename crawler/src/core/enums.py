from enum import StrEnum, IntEnum

from core.consts import DB_ERROR_LOG_LENGTH


class SubtitleType(StrEnum):
    vtt = "vtt"
    srt = "srt"


class VideoStatus(StrEnum):
    fetched = "fetched"
    downloaded = "downloaded"
    converted = "converted"
    subtitled = "subtitled"
    vtt_translated = "vtt_translated"
    meta_translated = "meta_translated"
    hls_ready = "hls_ready"
    uploaded = "uploaded"
    low_density = "low_density"
    oversized = "oversized"
    too_short = "too_short"
    retry_exceeded = "retry_exceeded"

    def log(self, e: Exception | str = None) -> str:
        n = DB_ERROR_LOG_LENGTH - len(self.value) - 3
        return f"[{self.value}] " + str(e)[:n]


class ThumbnailStatus(IntEnum):
    pending = 0
    downloaded = 1
    ytdlp_downloaded = 2
    failed = 4
