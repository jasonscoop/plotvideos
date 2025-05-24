import json
from pathlib import Path
import pytest

from src.lib.consts import SubtitleType
from src.utils.azure_stt_utils import flat_azure_result
from src.utils.azure_subtitle_utils import generate_subtitle, create_subtitle
from tests import SUBTITLES_DIR


@pytest.mark.parametrize("json_file",[
    "azure-results-661bb3bde2251.json"
])
def test_create_subtitle(json_file):
    json_path = SUBTITLES_DIR.joinpath(json_file)
    azure_results = json.loads(json_path.read_text())
    flatted_sub = flat_azure_result(azure_results)
    expected_vtt = json_path.with_suffix(".vtt").read_text()
    expected_srt = json_path.with_suffix(".srt").read_text()

    vtt = create_subtitle(flatted_sub, SubtitleType.vtt)
    srt = create_subtitle(flatted_sub, SubtitleType.srt)

    assert vtt == expected_vtt
    assert srt == expected_srt
