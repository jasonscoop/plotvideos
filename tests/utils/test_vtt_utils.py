import pytest

from src.utils.vtt_utils import is_valid_vtt, correct_vtt
from tests import SUBTITLES_DIR


@pytest.mark.parametrize("original_file, expected", [
    ("small/subtitle.vtt", True),
    ("small/es.vtt", False),
    ("small/zh.vtt", True),
    ("small/subtitle-format-invalid.vtt", False),
    ("vtt2/en.vtt", False),
    ("small/empty.vtt", False),
    ("small/empty2.vtt", True),
])
def test_is_valid_vtt(original_file, expected):
    vtt = SUBTITLES_DIR.joinpath(original_file).read_text()
    assert is_valid_vtt(vtt) == expected


@pytest.mark.parametrize("original_file", [
    "small/subtitle.vtt",
    "small/es.vtt",
    "small/zh.vtt",
    "vtt2/en.vtt",
    "small/empty.vtt",
    "small/empty2.vtt",
])
def test_correct_vtt(original_file):
    vtt = SUBTITLES_DIR.joinpath(original_file).read_text()
    assert is_valid_vtt(correct_vtt(vtt))
