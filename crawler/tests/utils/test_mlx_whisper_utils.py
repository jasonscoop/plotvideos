import pytest

from src.lib.schemas import StorePath
from src.utils.mlx_whisper_utils import mlx_whisper_transcribe


@pytest.mark.parametrize("host, original_id, filename", [
    ("www.youtube.com", "0001", "0001.webm"),
    ("www.youtube.com", "0002", "0002.webm"),
])
def test_mlx_whisper_transcribe(host, original_id, filename):
    path = StorePath(
        host=host,
        original_id=original_id,
        filename=filename
    )
    mlx_whisper_transcribe(path)
