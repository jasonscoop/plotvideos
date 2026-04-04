from enum import Enum
from typing import List


class Language(Enum):
    ENGLISH = ("en", "en-US", "English", "🇺🇸")
    GERMAN = ("de", "de-DE", "Deutsch", "🇩🇪")
    FRENCH = ("fr", "fr-FR", "Français", "🇫🇷")
    DUTCH = ("nl", "nl-NL", "Nederlands", "🇳🇱")
    JAPANESE = ("ja", "ja-JP", "日本語", "🇯🇵")
    KOREAN = ("ko", "ko-KR", "한국어", "🇰🇷")
    PORTUGUESE = ("pt", "pt-PT", "Português", "🇵🇹")
    ARABIC = ("ar", "ar-SA", "العربية", "🇸🇦")
    SPANISH = ("es", "es-ES", "Español", "🇪🇸")
    CHINESE = ("zh", "zh-CN", "简体中文", "🇨🇳")

    def __init__(self, code, locale, name, flag):
        self.code = code
        self.locale = locale
        self.native_name = name
        self.flag = flag

    @classmethod
    def from_code(cls, code) -> "Language":
        for lang in cls:
            if lang.code == code:
                return lang
        raise ValueError(f"Invalid language code: {code}")


    @classmethod
    def from_locale(cls, locale) -> "Language":
        for lang in cls:
            if lang.locale == locale:
                return lang
        raise ValueError(f"Invalid locale: {locale}")

    @classmethod
    def get_all(cls) -> List["Language"]:
        return list(cls)
