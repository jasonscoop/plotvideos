import json
from pathlib import Path

import pytest

from src.lib.enums import SubtitleType
from src.utils.azure_fast_transcription import transcribe_audio
from src.utils.azure_subtitle_utils import azure_stt_results_to_subtitle, get_texts_lang_codes, \
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


@pytest.mark.parametrize("path", [
    "/Users/garymeng/Downloads/youtube/cn.wav",
    "/Users/garymeng/Downloads/youtube/python.wav"
])
def test_generate_subtitle(path):
    audio_path = Path(path)
    try:
        azure_results = transcribe_audio(Path(path), ["en-US", "zh-CN"])
    except Exception as ex:
        pytest.fail(ex)
    audio_path.with_suffix(".json").write_text(json.dumps(azure_results, indent=2, ensure_ascii=False))

    vtt_content, subtitle_content = azure_fast_transcription_to_subtitle(azure_results, SubtitleType.vtt)
    audio_path.with_suffix(".vtt").write_text(vtt_content)


def test_azure_fast_transcription_to_subtitle():
    json_content = SUBTITLES_DIR.joinpath("fast/ja.json").read_text()
    vtt, content = azure_fast_transcription_to_subtitle(json.loads(json_content), SubtitleType.vtt)
    SUBTITLES_DIR.joinpath("fast/ja.vtt").write_text(vtt)
    SUBTITLES_DIR.joinpath("fast/ja.txt").write_text(content)

    json_content = SUBTITLES_DIR.joinpath("fast/clip3-en.json").read_text()
    vtt, content = azure_fast_transcription_to_subtitle(json.loads(json_content), SubtitleType.vtt)
    SUBTITLES_DIR.joinpath("fast/clip3-en.vtt").write_text(vtt)
    SUBTITLES_DIR.joinpath("fast/clip3-en.txt").write_text(content)
