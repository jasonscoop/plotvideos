from pathlib import Path
from typing import List

import requests

from src.lib.config import AZURE_SPEECH_REGION, AZURE_SPEECH_KEY
from src.utils.azure_stt_utils import media_to_wav
from src.utils.file_utils import save_json


def transcribe_audio(audio_path: Path, locales: List[str]) -> dict:
    endpoint = f"https://{AZURE_SPEECH_REGION}.api.cognitive.microsoft.com"
    url = f"{endpoint}/speechtotext/transcriptions:transcribe?api-version=2024-11-15"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
    }

    with open(audio_path, "rb") as audio_file:
        files = {
            "audio": audio_file,
            # "locales": locales,
        }
        response = requests.post(url, headers=headers, files=files)

    response.raise_for_status()
    return response.json()


if __name__ == '__main__':
    filepath = "/Users/garymeng/code/more/wuse/tests/files/videos/clip2.mp4"
    media_to_wav(Path(filepath), "clip2.wav")
    r = transcribe_audio(Path("clip2.wav"), ["hi-IN"])
    save_json("clip2.json", r)
