from typing import BinaryIO, Optional

import stt2vtt
from faster_whisper import WhisperModel

from crawler.core.config import (
    MODELS_DIR,
    WHISPER_DEVICE,
    WHISPER_COMPUTE_TYPE,
    WHISPER_CPU_THREADS,
    WHISPER_NUM_WORKERS,
    WHISPER_MODEL,
    WHISPER_BEAM_SIZE,
    WHISPER_DEVICE_INDEX,
    WHISPER_LOCAL_FILES_ONLY,
)

_whisper_model: WhisperModel = None


def get_whisper_model() -> WhisperModel:
    global _whisper_model
    if _whisper_model is None:
        _whisper_model = WhisperModel(
            model_size_or_path=WHISPER_MODEL,
            device=WHISPER_DEVICE,
            device_index=WHISPER_DEVICE_INDEX,
            compute_type=WHISPER_COMPUTE_TYPE,
            cpu_threads=WHISPER_CPU_THREADS,
            num_workers=WHISPER_NUM_WORKERS,
            download_root=MODELS_DIR.joinpath(WHISPER_MODEL).as_posix(),
            local_files_only=WHISPER_LOCAL_FILES_ONLY,
        )
    return _whisper_model


def whisper_transcribe(audio_data: BinaryIO, language: str = None) -> tuple[str, int]:
    transcribe_kwargs = {
        "audio": audio_data,
        "beam_size": WHISPER_BEAM_SIZE,
        "word_timestamps": True,
        "vad_filter": True,
        "vad_parameters": dict(min_silence_duration_ms=500),
    }

    if language:
        transcribe_kwargs["language"] = language

    segments, _ = get_whisper_model().transcribe(**transcribe_kwargs)

    segment_dicts = []
    word_count = 0
    for seg in segments:
        words = [
            {"start": w.start, "end": w.end, "word": w.word}
            for w in (seg.words or [])
        ]
        word_count += len(words)
        segment_dicts.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text,
            "words": words,
        })

    vtt_content = stt2vtt(segment_dicts)
    return vtt_content, word_count


def detect_audio_format(audio_data: bytes) -> Optional[str]:
    if len(audio_data) < 12:
        return None

    if audio_data[:3] == b'ID3' or audio_data[:2] in (b'\xff\xfb', b'\xff\xf3', b'\xff\xf2'):
        return '.mp3'
    if audio_data[:4] == b'RIFF' and audio_data[8:12] == b'WAVE':
        return '.wav'
    if audio_data[:4] == b'OggS':
        return '.ogg'
    if audio_data[:4] == b'fLaC':
        return '.flac'
    if audio_data[4:8] == b'ftyp':
        if b'M4A' in audio_data[8:20] or b'mp42' in audio_data[8:20]:
            return '.m4a'
        return '.mp4'
    if audio_data[:4] == b'\x1a\x45\xdf\xa3':
        return '.webm'

    return None

