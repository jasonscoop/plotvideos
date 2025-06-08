from enum import StrEnum, Enum
from typing import List, Optional


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
    skipped_due_to_zero_duration = "skipped_due_to_zero_duration"


class Language(Enum):
    ENGLISH = ("en", "en-US", "English", ["英文"])
    CHINESE = ("zh", "zh-CN", "简体中文", ["Chinese", "Simplified Chinese", "中文", "简中", "中字", "国语", "汉语"])
    HINDI = ("hi", "hi-IN", "हिन्दी", ["Hindi", "Hin"])
    SPANISH = ("es", "es-ES", "Español", ["Spanish", "ESP", "Castellano"])
    ARABIC = ("ar", "ar-SA", "العربية", ["Arabic", "Arabi"])
    FRENCH = ("fr", "fr-FR", "Français", ["French"])
    BENGALI = ("bn", "bn-BD", "বাংলা", ["Bengali", "Bangla"])
    PORTUGUESE = ("pt", "pt-PT", "Português", ["Portuguese", "Português Europeu", "Português Brasileiro"])
    RUSSIAN = ("ru", "ru-RU", "Русский", ["Russian"])
    URDU = ("ur", "ur-PK", "اردو", ["Urdu"])
    INDONESIAN = ("id", "id-ID", "Bahasa Indonesia", ["Indonesian", "Bahasa"])
    GERMAN = ("de", "de-DE", "Deutsch", ["German"])
    JAPANESE = ("ja", "ja-JP", "日本語", ["Japanese", "日文"])
    SWAHILI = ("sw", "sw-KE", "Kiswahili", ["Swahili"])

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

    @property
    def aliases(self) -> List[str]:
        return self.value[3]

    @classmethod
    def from_short_code(cls, short_code: str) -> Optional["Language"]:
        for lang in cls:
            if lang.short_code == short_code.lower():
                return lang

        return None

    @classmethod
    def from_long_code(cls, long_code: str) -> Optional["Language"]:
        for lang in cls:
            if lang.long_code.lower() == long_code.lower():
                return lang

        return None

    @classmethod
    def top4(cls) -> List["Language"]:
        return [cls.ENGLISH, cls.CHINESE, cls.HINDI, cls.SPANISH]
