import json
from pathlib import Path
import pytest

from src.lib.consts import SubtitleType
from src.utils.azure_stt_utils import flat_azure_result
from src.utils.azure_subtitle_utils import generate_subtitle, create_subtitle, simple_create_subtitle
from tests import SUBTITLES_DIR


@pytest.mark.parametrize("json_file",[
    # "azure-results-661bb3bde2251.json",
    "azure-results-youtube-tsYnuJI0u4I.json",
])
def test_create_subtitle(json_file):
    json_path = SUBTITLES_DIR.joinpath(json_file)
    azure_results = json.loads(json_path.read_text())
    flatted_sub = flat_azure_result(azure_results)

    vtt = create_subtitle(flatted_sub, SubtitleType.vtt)
    srt = create_subtitle(flatted_sub, SubtitleType.srt)

    Path("/Users/garymeng/code/more/wuse/tests/files/subtitles/azure-results-youtube-tsYnuJI0u4I.vtt").write_text(vtt)
    Path("/Users/garymeng/code/more/wuse/tests/files/subtitles/azure-results-youtube-tsYnuJI0u4I.srt").write_text(srt)

    assert vtt == json_path.with_suffix(".vtt").read_text()
    assert srt == json_path.with_suffix(".srt").read_text()


@pytest.mark.parametrize("json_file",[
    "661bb3bde2251-small.azure-result-4.json",
    "jiabin4.json",
])
def test_simple_create_subtitle(json_file):
    json_path = SUBTITLES_DIR.joinpath(json_file)
    azure_results = json.loads(json_path.read_text())
    vtt = simple_create_subtitle(azure_results, SubtitleType.vtt)

    json_path.with_suffix(".generated4.vtt").write_text(vtt)

    assert vtt == json_path.with_suffix(".generated4.vtt").read_text()
