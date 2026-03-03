from pathlib import Path

import pytest

from src.utils.video_ad_utils import StartAdTrimmer
from tests import VIDEOS_DIR


@pytest.mark.parametrize("video_path, expected", [
    ("clip1.mp4", "clip1_trimmed.mp4"),
    ("clip2.mp4", "clip2.mp4"),
    ("clip3.mp4", "clip3.mp4"),
])
def test_trim_ad(video_path: str, expected: str):
    full_video_path = VIDEOS_DIR / video_path
    assert StartAdTrimmer(full_video_path).trim_ad() == Path(full_video_path.parent / expected)
