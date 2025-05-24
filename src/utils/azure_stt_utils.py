import logging

import azure.cognitiveservices.speech as speechsdk
import json
from pydub import AudioSegment
import time
from pathlib import Path

from src.lib.config import AZURE_SPEECH_REGION, AZURE_SPEECH_KEY
from src.lib.schemas import FlattedSub, SubWord
from src.utils.log_utils import init_logging, log_time


@log_time
def media_to_wav(video_path: Path, wav_path: Path, target_sample_rate=16000) -> float:
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

    return len(audio) / 1000.0


@log_time
def get_azure_results(audio_path: Path, duration: float):
    # Configure speech recognition
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    # speech_config.speech_recognition_language = "en-US"

    # Enable detailed output with word-level timestamps
    speech_config.request_word_level_timestamps()
    speech_config.output_format = speechsdk.OutputFormat.Detailed

    # Configure timeouts (in milliseconds)
    speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "1000")
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "5000")
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "2000")

    # Create audio input
    audio_path_str = audio_path.as_posix() if isinstance(audio_path, Path) else audio_path
    audio_config = speechsdk.audio.AudioConfig(filename=audio_path_str)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    results = []
    done = False
    def handle_result(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            if evt.result.text.strip():  # Only process non-empty results
                results.append(json.loads(evt.result.json))
                logging.info(f"Recognized: {evt.result.text}")

    def handle_canceled(evt):
        logging.error(f"Recognition canceled: {evt.reason}")
        if evt.reason == speechsdk.CancellationReason.Error:
            logging.error(f"Error details: {evt.error_details}")
        nonlocal done
        done = True

    def handle_session_stopped(evt):
        logging.info("Session stopped")
        nonlocal done
        done = True

    speech_recognizer.recognized.connect(handle_result)
    speech_recognizer.session_stopped.connect(handle_session_stopped)
    speech_recognizer.canceled.connect(handle_canceled)

    # Start recognition
    speech_recognizer.start_continuous_recognition()

    # Wait for completion with timeout
    timeout = max(300, int(duration * 1.5))  # Either 5 minutes or 1.5x audio duration
    recognition_start = time.time()

    while not done and (time.time() - recognition_start) < timeout:
        time.sleep(0.5)

    # Stop recognition
    speech_recognizer.stop_continuous_recognition()
    time.sleep(2)  # Give it time to process final results

    return results


@log_time
def flat_azure_result(azure_results) -> FlattedSub:
    nbests = []
    for result_json in azure_results:
        if result_json.get("NBest", []):
            nbests.append(result_json["NBest"][0])

    if not nbests:
        logging.warning("No valid nbests were generated!")
        return FlattedSub()

    texts = []
    sub = FlattedSub()
    for best in nbests:
        texts.append(best["Display"])
        for word in best["Words"]:
            sub.words.append(SubWord(
                word=word["Word"],
                start_time=word["Offset"],
                end_time=word["Offset"] + word["Duration"],
            ))
    sub.text = " ".join(texts)

    return sub

