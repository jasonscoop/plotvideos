import pytest

from src.utils.whisper_utils import whisper_transcribe


@pytest.mark.parametrize("path", [
    "/Users/garymeng/Downloads/youtube/cn.wav",
    "/Users/garymeng/Downloads/youtube/python.wav"
])
def test_whisper_transcribe(path):
    whisper_transcribe(path)
