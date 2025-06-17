from enum import StrEnum

from src.lib.consts import DB_ERROR_LOG_LENGTH


class SubtitleType(StrEnum):
    vtt = "vtt"
    srt = "srt"


class VideoStatus(StrEnum):
    fetched = "fetched"
    downloaded = "downloaded"
    subtitled = "subtitled"
    converted = "converted"
    meta_translated = "meta_translated"
    vtt_translated = "vtt_translated"
    uploaded = "uploaded"
    published = "published"

    failed = "failed"

    def log(self, e: Exception | str = None) -> str:
        n = DB_ERROR_LOG_LENGTH - len(self.value) - 3
        return f"[{self.value}] " + str(e)[:n]
