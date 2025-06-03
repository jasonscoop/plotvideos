from enum import StrEnum, Enum
from typing import List


class TermType(StrEnum):
    """name is for code, value is for wp endpoint calling"""
    categories = "category"
    tags = "post_tag"


class SubtitleType(StrEnum):
    vtt = "vtt"
    srt = "srt"


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


class Language(Enum):
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
    def from_short_code(cls, short_code: str):
        for lang in cls:
            if lang.short_code == short_code.lower():
                return lang

        return cls.ENGLISH

    @classmethod
    def top4(cls) -> List[str]:
        return [
            cls.ENGLISH.long_code,
            cls.CHINESE.long_code,
            cls.HINDI.long_code,
            cls.SPANISH.long_code,
        ]
