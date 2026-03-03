from enum import StrEnum


class VideoStatus(StrEnum):
    fetched = "fetched"
    downloaded = "downloaded"
    converted = "converted"
    subtitled = "subtitled"
    vtt_translated = "vtt_translated"
    meta_translated = "meta_translated"
    uploaded = "uploaded"
    published = "published"
    failed = "failed"

