from pathlib import Path

import whisper
from pydub import AudioSegment

from src.lib.config import MODELS_DIR
from src.lib.schemas import PreDetectResult


def detect_talking_whisper(wav_path: Path):
    audio_path = wav_path if isinstance(wav_path, Path) else Path(wav_path)

    model = whisper.load_model("small", download_root=MODELS_DIR / "whisper")  # Or "base" for better accuracy
    result = whisper.transcribe(model=model,
                                audio=audio_path.as_posix(),
                                no_speech_threshold=0.75,
                                # Be more conservative: require stronger confidence in talking
                                logprob_threshold=-0.5,  # Raise the bar for accepting decoded text
                                compression_ratio_threshold=2.0,  # Reject outputs that look "repetitive" or like noise
                                temperature=0.0,  # Deterministic decoding, helps reduce randomness
                                verbose=False)
    speech_seconds = 0.0
    for segment in result.get("segments", []):
        start = segment["start"]
        end = segment["end"]
        speech_seconds += end - start

    total_seconds = len(AudioSegment.from_file(wav_path)) / 1000.0

    return PreDetectResult(
        text=result.get("text", "").strip(),
        lang=result.get("language", ""),
        speech_seconds=speech_seconds,
        total_seconds=total_seconds,
        speech_ratio=round(speech_seconds / total_seconds, 2),
    )
