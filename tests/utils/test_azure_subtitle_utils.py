import json

import pytest

from src.lib.enums import SubtitleType
from src.lib.models import Video
from src.utils.azure_subtitle_utils import azure_stt_results_to_subtitle, get_texts_lang_codes, generate_subtitle, \
    azure_fast_transcription_to_subtitle
from tests import SUBTITLES_DIR


@pytest.mark.parametrize("json_file", [
    "661bb3bde2251-small.azure-result-4.json",
    "jiabin4.json",
])
def test_simple_create_subtitle(json_file):
    json_path = SUBTITLES_DIR.joinpath(json_file)
    azure_results = json.loads(json_path.read_text())
    vtt = azure_stt_results_to_subtitle(azure_results, SubtitleType.vtt)

    json_path.with_suffix(".generated4.vtt").write_text(vtt)

    assert vtt == json_path.with_suffix(".generated4.vtt").read_text()


@pytest.mark.parametrize("texts, expected", [
    (["Hindi"], ["hi", "en"]),
    (["这是哪里？", "What is here?"], ["zh", "en"]),
    (["这是哪里？", "What is here?", "日本語"], ["zh", "en", "ja"]),
    (["我们很有希望！", "グが好きです", "What is here?", "Hindi"], ["zh", "en", "ja", "hi"]),
])
def test_get_texts_lang_codes(texts, expected):
    assert set(get_texts_lang_codes(texts)) == set(expected)


def test_generate_subtitle():
    assert generate_subtitle(Video(id=1, title="The Japanese man", filename="xhDw3Y5.mp4",
                                   tags=["Chinese"],
                                   categories=["Peace"],
                                   host="www.xhamster.com", original_id="xhDw3Y5",
                                   duration=60,
                                   keyword="The Japanese man"))


def test_azure_fast_transcription_to_subtitle():
    json_content = SUBTITLES_DIR.joinpath("fast/ja.json").read_text()
    vtt, content = azure_fast_transcription_to_subtitle(json.loads(json_content), SubtitleType.vtt)
    SUBTITLES_DIR.joinpath("fast/ja.vtt").write_text(vtt)
    SUBTITLES_DIR.joinpath("fast/ja.txt").write_text(content)

    json_content = SUBTITLES_DIR.joinpath("fast/clip3-en.json").read_text()
    vtt, content = azure_fast_transcription_to_subtitle(json.loads(json_content), SubtitleType.vtt)
    SUBTITLES_DIR.joinpath("fast/clip3-en.vtt").write_text(vtt)
    SUBTITLES_DIR.joinpath("fast/clip3-en.txt").write_text(content)
