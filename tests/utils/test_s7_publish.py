from src.lib.consts import BigLanguage, TermType
from src.service.s7_publish import create_or_get_term


def test_create_or_get_term():
    translations = {
        ("Flower", BigLanguage.JAPANESE): "花",
        ("Flower", BigLanguage.CHINESE): "花",
        ("Flower", BigLanguage.ENGLISH): "Flower",

        ("Flower", BigLanguage.HINDI): "फूल",
        ("Flower", BigLanguage.SPANISH): "Flor",
        ("Flower", BigLanguage.ARABIC): "ورد",
        ("Flower", BigLanguage.FRENCH): "Fleur",
        ("Flower", BigLanguage.BENGALI): "ফুল",
        ("Flower", BigLanguage.PORTUGUESE): "Flor",
        ("Flower", BigLanguage.RUSSIAN): "Цветок",
        ("Flower", BigLanguage.URDU): "پھول",
        ("Flower", BigLanguage.INDONESIAN): "Bunga",
        ("Flower", BigLanguage.GERMAN): "Blume",

        ("Flower", BigLanguage.SWAHILI): "Maua",
    }
    term_id = create_or_get_term("Flower", translations, TermType.category, BigLanguage.JAPANESE)
    assert isinstance(term_id, int)
