import pytest

from src.utils.video_watermarker_utils import WatermakerUtils
from tests import VIDEOS_DIR


@pytest.mark.parametrize("video_path, logo, expected", [
    ("clip1.mp4", "pornhub", True),
    ("clip2.mp4", "pornhub", True),
    ("clip3.mp4", "pornhub", True),
])
def test_has_watermark(video_path, logo, expected):
    assert WatermakerUtils(VIDEOS_DIR / video_path, logo).has_watermark() == expected
