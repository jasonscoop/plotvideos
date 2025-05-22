from enum import StrEnum

from src.utils.id_utils import PornhubIdExtractor, XhamsterIdExtractor, XvideosIdExtractor, EpornerIdExtractor, \
    YouJizzIdExtractor, RedTubeIdExtractor, YouPornIdExtractor, SpankBangIdExtractor

# Languages with Over 100 Million Total Speakers
SUPPORTED_LANGUAGES = {
    "en": "English",
    "zh": "Mandarin Chinese",
    "hi": "Hindi",
    "es": "Spanish",
    "ar": "Arabic",
    "fr": "French",
    "bn": "Bengali",
    "pt": "Portuguese",
    "ru": "Russian",
    "ur": "Urdu",
    "id": "Indonesian",
    "de": "German",
    "ja": "Japanese",
    "sw": "Swahili",
    "mr": "Marathi",
    "te": "Telugu",
    "tr": "Turkish"
}


class VideoStatus(StrEnum):
    added = "added"
    downloaded = "downloaded"
    subtitle_downloaded = "subtitle_downloaded"
    subtitle_translated = "subtitle_translated"
    published = "published"

    download_failed = "download_failed"
    subtitle_download_failed = "subtitle_download_failed"
    subtitle_translate_failed = "subtitle_translate_failed"
    publish_failed = "publish_failed"


ID_EXTRACTOR_MAP = {
    "www.pornhub.com": PornhubIdExtractor,
    "www.xhamster.com": XhamsterIdExtractor,
    "www.xvideos.com": XvideosIdExtractor,
    "www.eporner.com": EpornerIdExtractor,
    "www.youjizz.com": YouJizzIdExtractor,
    "www.redtube.com": RedTubeIdExtractor,
    "www.youporn.com": YouPornIdExtractor,
    "www.pornhd.com": PornhubIdExtractor,
    "spankbang.com": SpankBangIdExtractor,
}

SUPPORTED_VIDEO_EXTENSIONS = {"3gp", "flv", "mp4", "webm"}
