from enum import StrEnum


class VideoStatus(StrEnum):
    fetched = "fetched"
    downloading = "downloading"
    downloaded = "downloaded"
    converting = "converting"
    converted = "converted"
    subtitling = "subtitling"
    subtitled = "subtitled"
    vtt_translating = "vtt_translating"
    vtt_translated = "vtt_translated"
    meta_translating = "meta_translating"
    meta_translated = "meta_translated"
    uploading = "uploading"
    uploaded = "uploaded"
    publishing = "publishing"
    published = "published"

