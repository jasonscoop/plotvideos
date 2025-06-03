import json

from src.lib.enums import Language
from src.utils.llm_utils import translate_vtt, translate_video_content
from tests import SUBTITLES_DIR


def test_ask_azure_openai():
    vtt = SUBTITLES_DIR.joinpath("azure-results-661bb3bde2251.vtt").read_text()
    expected = SUBTITLES_DIR.joinpath("azure-results-661bb3bde2251.zh-CN.vtt").read_text()

    actual = translate_vtt(vtt, Language.CHINESE)
    assert actual == expected


def test_translate_video_content():
    actual = translate_video_content({
        "title": "what is you name?",
        "description": "here is best friend",
        "tags": ["Home", "Sun"],
        "categories": ["Sea", "Football"]
    }, Language.CHINESE)

    expected = '{"categories": ["海", "足球"],"description": "这是最好的朋友","tags": ["家", "太阳"],"title": "你叫什么名字？"}'
    assert actual == json.loads(expected)
