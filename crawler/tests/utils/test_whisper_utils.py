import pytest

from src.lib.schemas import StorePath
from src.utils.whisper_utils import whisper_transcribe


@pytest.mark.parametrize("host, original_id, filename", [
    ("www.youtube.com", "0001", "0001.webm"),
    ("www.youtube.com", "0002", "0002.webm"),
])
def test_whisper_transcribe(host, original_id, filename):
    path = StorePath(
        host=host,
        original_id=original_id,
        filename=filename
    )
    whisper_transcribe(path)
