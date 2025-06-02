from src.lib.consts import Language, TermType
from src.service.s7_publish import create_or_get_term


def test_create_or_get_term():
    translations = {
        ("Flower", Language.JAPANESE): "花",
        ("Flower", Language.CHINESE): "花",
        ("Flower", Language.ENGLISH): "Flower",

        ("Flower", Language.HINDI): "फूल",
        ("Flower", Language.SPANISH): "Flor",
        ("Flower", Language.ARABIC): "ورد",
        ("Flower", Language.FRENCH): "Fleur",
        ("Flower", Language.BENGALI): "ফুল",
        ("Flower", Language.PORTUGUESE): "Flor",
        ("Flower", Language.RUSSIAN): "Цветок",
        ("Flower", Language.URDU): "پھول",
        ("Flower", Language.INDONESIAN): "Bunga",
        ("Flower", Language.GERMAN): "Blume",

        ("Flower", Language.SWAHILI): "Maua",
    }
    term_id = create_or_get_term("Flower", translations, TermType.category, Language.JAPANESE)
    assert isinstance(term_id, int)
