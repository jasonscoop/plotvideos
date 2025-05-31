from enum import StrEnum, Enum
from typing import List

from loguru import logger

from src.utils.id_utils import PornhubIdExtractor, XhamsterIdExtractor, XvideosIdExtractor, EpornerIdExtractor, \
    YouJizzIdExtractor, RedTubeIdExtractor, YouPornIdExtractor, SpankBangIdExtractor

DB_ERROR_LOG_LENGTH = 1000


class BigLanguage(Enum):
    ENGLISH = ("en", "en-US", "English")
    CHINESE = ("zh", "zh-CN", "简体中文")
    HINDI = ("hi", "hi-IN", "हिन्दी")
    SPANISH = ("es", "es-ES", "Español")
    ARABIC = ("ar", "ar-SA", "العربية")
    FRENCH = ("fr", "fr-FR", "Français")
    BENGALI = ("bn", "bn-BD", "বাংলা")
    PORTUGUESE = ("pt", "pt-PT", "Português")
    RUSSIAN = ("ru", "ru-RU", "Русский")
    URDU = ("ur", "ur-PK", "اردو")
    INDONESIAN = ("id", "id-ID", "Bahasa Indonesia")
    GERMAN = ("de", "de-DE", "Deutsch")
    JAPANESE = ("ja", "ja-JP", "日本語")
    SWAHILI = ("sw", "sw-KE", "Kiswahili")

    @property
    def short_code(self) -> str:
        # iso639_code
        return self.value[0]

    @property
    def long_code(self) -> str:
        # bcp47_code
        return self.value[1]

    @property
    def native_name(self) -> str:
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

    failed_downloaded = "failed_downloaded"
    failed_subtitled = "failed_subtitled"
    failed_meta_translated = "failed_meta_translated"
    failed_vtt_translated = "failed_vtt_translated"
    failed_uploaded = "failed_uploaded"
    failed_published = "failed_published"

    skipped_due_to_size = "skipped_due_to_size"
    skipped_due_to_low_speech = "skipped_due_to_low_speech"
    skipped_due_to_short_speech = "skipped_due_to_short_speech"
    skipped_due_to_empty_subtitle = "skipped_due_to_empty_subtitle"


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

BUNNEY_COLLECTION_MAP = {
    "www.pornhub.com": "e3edc1ee-ecab-4451-bff2-fdeafb779415",
    "www.xhamster.com": "af16977f-15cf-4e1c-8b85-b6bf6dfc59e2",
    "www.xvideos.com": "a9d247b3-b562-44ed-8c6f-aa05d4532811",
    "www.eporner.com": "0ed26c1b-56ad-4057-b89e-3cc013b773ed",
    "www.youjizz.com": "49ed13c7-1491-4f55-9728-e78ad45814a4",
    "www.redtube.com": "e5682a25-bd3a-4111-8e60-8ad077ff6fe9",
    "www.youporn.com": "dcf8cba2-896e-41f1-b6aa-ef281b27b47d",
    "www.pornhd.com": "2df6932e-6079-47a8-b469-57eeda34a0cd",
    "spankbang.com": "97e2e3e6-0103-4179-898b-94b0bb7ed1b5",
}

VIDEO_EMBED_TEMPLATE = """<!-- wp:bunnycdn/block-stream-video {"library_id":"{library_id}","collection_id":"","video_id":"{video_id}","token_authentication":false,"responsive":true} -->
<div class="wp-block-bunnycdn-block-stream-video"><div style="position:relative;padding-top:56.25%;width:100%"><iframe src="https://iframe.mediadelivery.net/embed/{library_id}/{video_id}?autoplay=false&amp;loop=false&amp;muted=false&amp;preload=false&amp;responsive=true" loading="lazy" style="border:0;position:absolute;top:0;height:100%;width:100%" allow="accelerometer;gyroscope;autoplay;encrypted-media;picture-in-picture;" allowfullscreen></iframe></div></div>
<!-- /wp:bunnycdn/block-stream-video -->"""
