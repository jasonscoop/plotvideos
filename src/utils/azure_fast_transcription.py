import json
from pathlib import Path
from typing import List

import requests

from src.lib.config import AZURE_SPEECH_REGION, AZURE_SPEECH_KEY
from src.utils.file_utils import save_json


def transcribe_audio(audio_path: Path, locales: List[str]) -> dict:
    """
    https://learn.microsoft.com/en-us/azure/ai-services/speech-service/fast-transcription-create?tabs=locale-specified
    https://learn.microsoft.com/en-us/rest/api/speechtotext/transcriptions/transcribe?view=rest-speechtotext-2024-11-15
    https://github.com/Azure/azure-rest-api-specs/blob/7fafef79f974d996d4d9f3474bfee09e5d9bdc3b/specification/cognitiveservices/data-plane/Speech/SpeechToText/preview/2024-05-15-preview/speechtotext.json#L6168
    """
    assert Path(audio_path).is_file(), f"{audio_path} is not found"

    endpoint = f"https://{AZURE_SPEECH_REGION}.api.cognitive.microsoft.com"
    url = f"{endpoint}/speechtotext/transcriptions:transcribe?api-version=2024-11-15"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
    }

    config = {
        "locale": locales,
        "profanityFilterMode": "None"
    }

    files = {
        "audio": open(audio_path, "rb"),
        "definition": ("", json.dumps(config), 'application/json')
    }
    response = requests.post(url, headers=headers, files=files)

    response.raise_for_status()
    return response.json()


if __name__ == '__main__':
    # filepath = "/Users/garymeng/code/more/wuse/works/videos/www.xvideos.com/kh/khfudok557d/khfudok557d.mp4"
    # media_to_mp3(Path(filepath), "khfudok557d.mp3")
    r = transcribe_audio(Path("/Users/garymeng/code/more/wuse/khfudok557d.mp3"), ["ja-JP", "en-US"])
    save_json("khfudok557d.json", r)
