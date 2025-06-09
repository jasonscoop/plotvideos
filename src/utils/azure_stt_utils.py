import json
from pathlib import Path
from threading import Event
from typing import List

import azure.cognitiveservices.speech as speechsdk
from loguru import logger
from pydub import AudioSegment

from src.lib.config import AZURE_SPEECH_REGION, AZURE_SPEECH_KEY


def media_to_wav(video_path: Path, wav_path: Path, target_sample_rate=16000) -> int:
    audio = AudioSegment.from_file(video_path)

    # Optimize for speech recognition:
    # 1. Convert to mono
    # 2. Set sample rate to 16kHz
    # 3. Normalize volume
    audio = audio.set_channels(1).set_frame_rate(target_sample_rate).normalize()

    # Export with optimized parameters
    audio.export(
        wav_path,
        format='wav',
        parameters=[
            "-ac", "1",  # mono
            "-ar", str(target_sample_rate),  # sample rate
            "-acodec", "pcm_s16le"  # 16-bit PCM
        ]
    )

    return round(len(audio) / 1000)


def get_azure_results(audio_path: Path, duration: float, final_lang_codes: List[str]):
    assert Path(audio_path).exists(), f"Audio file [{audio_path}] not found"

    # Configure speech recognition
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    # speech_config.speech_recognition_language = "en-US"

    auto_detect_source_language_config = speechsdk.languageconfig.AutoDetectSourceLanguageConfig(
        languages=final_lang_codes,
    )

    # Enable detailed output with word-level timestamps
    speech_config.set_profanity(speechsdk.enums.ProfanityOption.Raw)
    speech_config.request_word_level_timestamps()
    speech_config.output_format = speechsdk.OutputFormat.Detailed

    # Configure segmentation for shorter segments
    # IMPORTANT: Use correct property names and valid ranges from latest documentation

    # Strategy options: "Default", "Time", "Semantic"
    # - Default: Standard Azure behavior
    # - Semantic: AI-based phrase detection (no control properties)
    # speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationStrategy, "Semantic")
    # speech_config.enable_dictation()

    # - Time: Control via silence timeout and max time
    speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationStrategy, "Default")
    # Silence timeout: Range [100, 5000] milliseconds
    # Lower values = more frequent breaks, higher values = longer segments
    speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "100")  # 0.1 seconds
    # Maximum segment length, This prevents extremely long segments
    speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationMaximumTimeMs, "20000")  # 20 seconds max

    # Connection timeouts (these are different from segmentation)
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "3000")
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "1000")

    # Create audio input
    audio_path_str = audio_path.as_posix() if isinstance(audio_path, Path) else audio_path
    audio_config = speechsdk.audio.AudioConfig(filename=audio_path_str)
    speech_recognizer = speechsdk.SpeechRecognizer(
        speech_config=speech_config,
        audio_config=audio_config,
        auto_detect_source_language_config=auto_detect_source_language_config
    )

    results = []
    done_event = Event()

    def handle_result(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            if evt.result.text.strip():  # Only process non-empty results
                results.append(json.loads(evt.result.json))
                logger.info(f"Recognized: {evt.result.text}")

    def handle_canceled(evt):
        logger.error(f"Recognition canceled, reason: {evt.reason}")
        if evt.reason == speechsdk.CancellationReason.Error:
            logger.error(f"Error details: {evt.error_details}")
        done_event.set()

    def handle_session_stopped(evt):
        logger.info(f"Session stopped, reason: {evt.reason}")
        done_event.set()

    speech_recognizer.recognized.connect(handle_result)
    speech_recognizer.session_stopped.connect(handle_session_stopped)
    speech_recognizer.canceled.connect(handle_canceled)

    # Start recognition
    speech_recognizer.start_continuous_recognition()

    # Wait for completion with timeout
    timeout = max(300, int(duration * 1.5))  # Either 5 minutes or 1.5x audio duration
    done_event.wait(timeout)

    # Stop recognition
    speech_recognizer.stop_continuous_recognition()
