from loguru import logger
from enum import StrEnum, Enum
from typing import List

from src.utils.id_utils import PornhubIdExtractor, XhamsterIdExtractor, XvideosIdExtractor, EpornerIdExtractor, \
    YouJizzIdExtractor, RedTubeIdExtractor, YouPornIdExtractor, SpankBangIdExtractor


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
    MARATHI = ("mr", "mr-IN", "Marathi")
    TELUGU = ("te", "te-IN", "Telugu")
    TURKISH = ("tr", "tr-TR", "Turkish")

    @property
    def iso639_code(self) -> str:
        return self.value[0]

    @property
    def bcp47_code(self) -> str:
        return self.value[1]

    @property
    def full_name(self) -> str:
        return self.value[2]

    @classmethod
    def from_short_code(cls, code: str):
        for lang in cls:
            if lang.iso639_code == code.lower():
                return lang

        logger.error(f"[{code}] Language not found, set to default")
        return cls.ENGLISH

    @classmethod
    def top4(cls) -> List[str]:
        return [
            cls.ENGLISH.bcp47_code,
            cls.CHINESE.bcp47_code,
            cls.HINDI.bcp47_code,
            cls.SPANISH.bcp47_code,
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
    added = "added"
    downloaded = "downloaded"
    subtitle_downloaded = "subtitle_downloaded"
    subtitle_translated = "subtitle_translated"
    published = "published"

    download_failed = "download_failed"
    subtitle_download_failed = "subtitle_download_failed"
    subtitle_translate_failed = "subtitle_translate_failed"
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

SUPPORTED_VIDEO_EXTENSIONS = {"3gp", "flv", "mp4", "webm"}
