import pytest

from src.utils.vtt_utils import is_valid_vtt
from tests import SUBTITLES_DIR


@pytest.mark.parametrize("original_file, expected", [
    ("small/subtitle.vtt", True),
    ("small/es.vtt", False),
    ("small/zh.vtt", True),
    ("small/subtitle-format-invalid.vtt", False),
])
def test_is_valid_vtt(original_file, expected):
    vtt = SUBTITLES_DIR.joinpath(original_file).read_text()
    assert is_valid_vtt(vtt) == expected

    assert is_valid_vtt("") is False
