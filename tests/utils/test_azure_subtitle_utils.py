import json
import pytest

from src.lib.consts import SubtitleType
from src.utils.azure_subtitle_utils import azure_stt_results_to_subtitle
from tests import SUBTITLES_DIR


@pytest.mark.parametrize("json_file",[
    "661bb3bde2251-small.azure-result-4.json",
    "jiabin4.json",
])
def test_simple_create_subtitle(json_file):
    json_path = SUBTITLES_DIR.joinpath(json_file)
    azure_results = json.loads(json_path.read_text())
    vtt = azure_stt_results_to_subtitle(azure_results, SubtitleType.vtt)

    json_path.with_suffix(".generated4.vtt").write_text(vtt)

    assert vtt == json_path.with_suffix(".generated4.vtt").read_text()
