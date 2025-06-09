import json

import requests

from src.lib.config import AZURE_SPEECH_REGION, AZURE_SPEECH_KEY
from src.utils.file_utils import save_json


def transcribe_audio(audio_path: str, locales: str) -> dict:
    endpoint = f"https://{AZURE_SPEECH_REGION}.api.cognitive.microsoft.com"
    url = f"{endpoint}/speechtotext/transcriptions:transcribe?api-version=2024-11-15"
    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
    }
    transcribe_definition = {
        "locale": ','.join(locales),
        "displayName": "My Transcription"
    }

    with open(audio_path, "rb") as audio_file:
        files = {
            "audio": audio_file,
            "definition": (None, json.dumps(transcribe_definition), "application/json")
        }
        response = requests.post(url, headers=headers, files=files)

    response.raise_for_status()
    return response.json()


if __name__ == '__main__':
    filepath = "/Users/garymeng/code/more/wuse/works/videos/xh/xh/xhDw3Y5/audio.wav"
    r = transcribe_audio(filepath, "")
    save_json("fast3.json", r)
