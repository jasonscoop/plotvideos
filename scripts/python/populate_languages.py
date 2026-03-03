from crawler.lib.connection import get_db
from crawler.lib.models import Language


def populate_languages():
    with get_db() as session:
        # Check if languages already exist
        if session.query(Language).first():
            print("Languages already populated")
            return

        # Define languages data
        languages = [
            ("en", "en-US", "English", ["英文"]),
            ("zh", "zh-CN", "简体中文", ["Chinese", "Simplified Chinese", "中文", "简中", "中字", "国语", "汉语"]),
            ("hi", "hi-IN", "हिन्दी", ["Hindi", "Hin"]),
            ("es", "es-ES", "Español", ["Spanish", "ESP", "Castellano"]),
            ("ar", "ar-SA", "العربية", ["Arabic", "Arabi"]),
            ("fr", "fr-FR", "Français", ["French"]),
            ("bn", "bn-BD", "বাংলা", ["Bengali", "Bangla"]),
            ("pt", "pt-PT", "Português", ["Portuguese", "Português Europeu", "Português Brasileiro"]),
            ("ru", "ru-RU", "Русский", ["Russian"]),
            ("ur", "ur-PK", "اردو", ["Urdu"]),
            ("id", "id-ID", "Bahasa Indonesia", ["Indonesian", "Bahasa"]),
            ("de", "de-DE", "Deutsch", ["German"]),
            ("ja", "ja-JP", "日本語", ["Japanese", "日文"]),
            ("sw", "sw-KE", "Kiswahili", ["Swahili"])
        ]

        # Create language records
        for code, locale, native_name, aliases in languages:
            language = Language(
                code=code,
                locale=locale,
                native_name=native_name,
                aliases=aliases
            )
            session.add(language)

        session.commit()
        print("Successfully populated languages")


if __name__ == "__main__":
    populate_languages()
