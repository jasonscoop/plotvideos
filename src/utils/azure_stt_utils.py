import json
import subprocess
from pathlib import Path
from threading import Event
from typing import List

import azure.cognitiveservices.speech as speechsdk
from loguru import logger
from tenacity import stop_after_attempt, retry, wait_fixed

from src.lib.config import AZURE_SPEECH_REGION, AZURE_SPEECH_KEY


def get_video_duration(video_path: Path) -> int:
    command = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return round(float(result.stdout.strip()))


@retry(wait=wait_fixed(1), stop=stop_after_attempt(3), reraise=True)
def media_to_wav(video_path: Path, wav_path: Path, target_sample_rate=16000):
    command = [
        "ffmpeg",
        "-i", str(video_path),
        "-ac", "1",  # mono
        "-ar", str(target_sample_rate),  # sample rate
        "-acodec", "pcm_s16le",  # 16-bit PCM
        "-y",  # overwrite output
        str(wav_path)
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


def media_to_mp3(video_path: Path, mp3_path: Path, bitrate="192k"):
    command = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",  # disable video
        "-ac", "2",  # stereo
        "-ab", bitrate,  # audio bitrate
        "-ar", "44100",  # sample rate (optional, common for MP3)
        "-y",  # overwrite output
        str(mp3_path)
    ]
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)


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
    speech_config.enable_dictation()

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

    def handle_session_started(evt):
        logger.info("Recognize started.")

    speech_recognizer.session_started.connect(handle_session_started)
    speech_recognizer.recognized.connect(handle_result)
    speech_recognizer.session_stopped.connect(handle_session_stopped)
    speech_recognizer.canceled.connect(handle_canceled)

    # Start recognition
    speech_recognizer.start_continuous_recognition()

    # Wait for completion with timeout
    timeout = max(300, int(duration * 1.5))  # Either 5 minutes or 1.5x audio duration
    done = done_event.wait(timeout)
    if not done:
        speech_recognizer.stop_continuous_recognition()
        raise RuntimeError(f"Subtitling timed out waiting for {duration} seconds.")

    return results
