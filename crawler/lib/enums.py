from enum import StrEnum, IntEnum

from crawler.lib.consts import DB_ERROR_LOG_LENGTH


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
    uploaded = "uploaded"
    published = "published"

    def log(self, e: Exception | str = None) -> str:
        n = DB_ERROR_LOG_LENGTH - len(self.value) - 3
        return f"[{self.value}] " + str(e)[:n]


class ThumbnailStatus(IntEnum):
    pending = 0
    downloaded = 1
    ytdlp_downloaded = 2
    failed = 4
