from src.lib.consts import BigLanguage
from src.utils.llm_utils import ask_azure_openai
from tests import SUBTITLES_DIR


def test_ask_azure_openai():
    vtt = SUBTITLES_DIR.joinpath("azure-results-661bb3bde2251.vtt").read_text()
    expected = SUBTITLES_DIR.joinpath("azure-results-661bb3bde2251.zh-CN.vtt").read_text()

    actual = ask_azure_openai(vtt, BigLanguage.CHINESE)
    assert actual == expected
