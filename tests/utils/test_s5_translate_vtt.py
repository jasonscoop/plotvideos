import pytest

from src.lib.enums import Language
from src.service.s5_translate_vtt import translate_vtt_content
from tests import SUBTITLES_DIR


@pytest.mark.parametrize("original_file, lang, expected_file", [
    ("small/subtitle.vtt", Language.CHINESE, "small/zh.vtt"),
    ("small/subtitle.vtt", Language.SPANISH, "small/es.vtt"),
])
def test_translate_vtt_content(original_file: str, lang: Language, expected_file: str):
    vtt = SUBTITLES_DIR.joinpath(original_file).read_text()
    expected = SUBTITLES_DIR.joinpath(expected_file).read_text()

    actual = translate_vtt_content(vtt, lang)
    assert actual == expected
