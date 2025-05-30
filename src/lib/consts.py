from enum import StrEnum, Enum
from typing import List

from loguru import logger

from src.utils.id_utils import PornhubIdExtractor, XhamsterIdExtractor, XvideosIdExtractor, EpornerIdExtractor, \
    YouJizzIdExtractor, RedTubeIdExtractor, YouPornIdExtractor, SpankBangIdExtractor

DB_ERROR_LOG_LENGTH = 1000


class BigLanguage(Enum):
    ENGLISH = ("en", "en-US", "English")
    CHINESE = ("zh", "zh-CN", "Mandarin Chinese")
    HINDI = ("hi", "hi-IN", "Hindi")
    SPANISH = ("es", "es-ES", "Spanish")
    ARABIC = ("ar", "ar-SA", "Arabic")
    FRENCH = ("fr", "fr-FR", "French")
    BENGALI = ("bn", "bn-BD", "Bengali")
    PORTUGUESE = ("pt", "pt-PT", "Portuguese")
    RUSSIAN = ("ru", "ru-RU", "Russian")
    URDU = ("ur", "ur-PK", "Urdu")
    INDONESIAN = ("id", "id-ID", "Indonesian")
    GERMAN = ("de", "de-DE", "German")
    JAPANESE = ("ja", "ja-JP", "Japanese")
    SWAHILI = ("sw", "sw-KE", "Swahili")

    @property
    def short_code(self) -> str:
        # iso639_code
        return self.value[0]

    @property
    def long_code(self) -> str:
        # bcp47_code
        return self.value[1]

    @property
    def full_name(self) -> str:
        return self.value[2]

    @classmethod
    def from_short_code(cls, code: str):
        for lang in cls:
            if lang.short_code == code.lower():
                return lang

        logger.error(f"[{code}] Language not found, set to default")
        return cls.ENGLISH

    @classmethod
    def top4(cls) -> List[str]:
        return [
            cls.ENGLISH.long_code,
            cls.CHINESE.long_code,
            cls.HINDI.long_code,
            cls.SPANISH.long_code,
        ]


FASTTEXT_LANG_ALIAS = {
    # Chinese and Dialects
    "zh": "zh",
    "zh-cn": "zh",
    "zh-tw": "zh",
    "yue": "zh",  # Cantonese
    "wuu": "zh",  # Shanghainese
    "hak": "zh",  # Hakka
    "nan": "zh",  # Min Nan
    "lzh": "zh",  # Classical Chinese
    "cdo": "zh",  # Min Dong
    "hsn": "zh",  # Xiang (Hunanese)
    "xmf": "zh",  # 🛑 Mistaken as Chinese – normalize
}


class VideoStatus(StrEnum):
    fetched = "fetched"
    downloaded = "downloaded"
    subtitled = "subtitled"
    meta_translated = "meta_translated"
    vtt_translated = "vtt_translated"
    uploaded = "uploaded"
    published = "published"

    download_failed = "download_failed"
    subtitle_failed = "subtitle_failed"
    meta_translate_failed = "meta_translate_failed"
    vtt_translate_failed = "vtt_translate_failed"
    upload_failed = "upload_failed"
    publish_failed = "publish_failed"


class SubtitleType(StrEnum):
    vtt = "vtt"
    srt = "srt"


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

VIDEO_EMBED_TEMPLATE = """<!-- wp:bunnycdn/block-stream-video {"library_id":"{library_id}","collection_id":"","video_id":"{video_id}","token_authentication":false,"responsive":true} -->
<div class="wp-block-bunnycdn-block-stream-video"><div style="position:relative;padding-top:56.25%;width:100%"><iframe src="https://iframe.mediadelivery.net/embed/{library_id}/{video_id}?autoplay=false&amp;loop=false&amp;muted=false&amp;preload=false&amp;responsive=true" loading="lazy" style="border:0;position:absolute;top:0;height:100%;width:100%" allow="accelerometer;gyroscope;autoplay;encrypted-media;picture-in-picture;" allowfullscreen></iframe></div></div>
<!-- /wp:bunnycdn/block-stream-video -->"""
