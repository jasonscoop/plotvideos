import logging

import azure.cognitiveservices.speech as speechsdk
import json
import datetime
import os
from pydub import AudioSegment
import time
from pathlib import Path
import re

from src.lib.config import AZURE_SPEECH_REGION, AZURE_SPEECH_KEY
from src.utils.log_utils import init_logging


def split_text_by_words(text, words, max_length=50):
    """
    Split text into segments using word timing information.
    """
    if len(text) <= max_length:
        return [(text, words[0], words[-1])]

    segments = []
    current_segment = []
    current_words = []
    current_length = 0

    for word_data in words:
        word = word_data.get("Word", "")
        word_len = len(word)

        # Check if adding this word would exceed max length
        if current_length + word_len + 1 > max_length and current_segment:
            # Join current segment and add to results
            segment_text = " ".join(current_segment)
            segments.append((segment_text, current_words[0], current_words[-1]))
            # Start new segment
            current_segment = [word]
            current_words = [word_data]
            current_length = word_len
        else:
            # Add word to current segment
            current_segment.append(word)
            current_words.append(word_data)
            current_length += word_len + 1  # +1 for space

    # Add remaining segment if any
    if current_segment:
        segment_text = " ".join(current_segment)
        segments.append((segment_text, current_words[0], current_words[-1]))

    return segments


def convert_to_wav(input_path, target_sample_rate=16000):
    start_time = time.time()
    audio = AudioSegment.from_file(input_path)
    duration = len(audio) / 1000.0  # Duration in seconds

    # Optimize for speech recognition:
    # 1. Convert to mono
    # 2. Set sample rate to 16kHz
    # 3. Normalize volume
    audio = audio.set_channels(1).set_frame_rate(target_sample_rate).normalize()
    wav_path = os.path.join(os.path.dirname(input_path), f"{Path(input_path).stem}.wav")

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

    end_time = time.time()
    logging.info(f"Converted {input_path} to {wav_path}, take {time.time() - start_time:.2f} seconds")
    logging.info(f"Audio duration: {duration}, ")
    return wav_path, duration


def audio_to_srt(audio_path, duration, output_path):
    start_time = time.time()

    # Configure speech recognition
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_recognition_language = "en-US"

    # Enable detailed output with word-level timestamps
    speech_config.request_word_level_timestamps()
    speech_config.output_format = speechsdk.OutputFormat.Detailed

    # Configure timeouts (in milliseconds)
    speech_config.set_property(speechsdk.PropertyId.Speech_SegmentationSilenceTimeoutMs, "1000")
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_InitialSilenceTimeoutMs, "5000")
    speech_config.set_property(speechsdk.PropertyId.SpeechServiceConnection_EndSilenceTimeoutMs, "2000")

    # Create audio input
    audio_config = speechsdk.audio.AudioConfig(filename=wav_path)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print(f"Starting recognition for audio file: {audio_path}")
    print(f"Duration: {duration:.2f} seconds")

    results = []
    done = False

    def handle_result(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            if evt.result.text.strip():  # Only process non-empty results
                results.append(evt.result.json)
                print(f"Recognized: {evt.result.text}")

    def handle_canceled(evt):
        print(f"Recognition canceled: {evt.reason}")
        if evt.reason == speechsdk.CancellationReason.Error:
            print(f"Error details: {evt.error_details}")
        nonlocal done
        done = True

    def handle_session_stopped(evt):
        print("Session stopped")
        nonlocal done
        done = True

    speech_recognizer.recognized.connect(handle_result)
    speech_recognizer.session_stopped.connect(handle_session_stopped)
    speech_recognizer.canceled.connect(handle_canceled)

    # Start recognition
    speech_recognizer.start_continuous_recognition()

    # Wait for completion with timeout
    timeout = max(300, duration * 1.5)  # Either 5 minutes or 1.5x audio duration
    recognition_start = time.time()

    while not done and (time.time() - recognition_start) < timeout:
        time.sleep(0.5)

    # Stop recognition
    speech_recognizer.stop_continuous_recognition()
    time.sleep(2)  # Give it time to process final results

    print(f"Recognition completed in {time.time() - recognition_start:.2f} seconds")
    print(f"Found {len(results)} segments")

    if not results:
        print("Warning: No recognition results were obtained!")
        return

    def json_to_srt(json_results):
        entries = []
        counter = 1

        def format_time(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace(".", ",")

        for result_json in json_results:
            try:
                result = json.loads(result_json)
                if not result.get("NBest", []):
                    continue

                best_result = result["NBest"][0]
                words = best_result.get("Words", [])
                if not words:
                    continue

                text = best_result.get("Display", "").strip()
                if not text:
                    continue

                # Get word-level segments with accurate timing
                segments = split_text_by_words(text, words)

                for segment_text, first_word, last_word in segments:
                    # Calculate precise timing for each segment
                    start_time = float(first_word["Offset"]) / 10_000_000
                    end_time = (float(last_word["Offset"]) + float(last_word["Duration"])) / 10_000_000

                    # Add a small gap between segments for readability
                    if counter > 1:
                        start_time += 0.05

                    entry = f"{counter}\n{format_time(start_time)} --> {format_time(end_time)}\n{segment_text}\n"
                    entries.append(entry)
                    counter += 1

            except Exception as e:
                print(f"Warning: Error processing result: {e}")
                continue

        return '\n'.join(entries)

    # Generate SRT
    srt_output = json_to_srt(results)

    if not srt_output.strip():
        print("Warning: No valid entries were generated!")
        return

    # Save SRT file
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(srt_output)

    print(f"Total processing time: {time.time() - start_time:.2f} seconds")
    print(f"Subtitle saved to: {output_path}")


if __name__ == '__main__':
    init_logging("stt")
    wav_path, duration = convert_to_wav("/Users/garymeng/code/more/wuse/works/661bb3bde2251.mp4")
    audio_to_srt(wav_path, duration, "/Users/garymeng/code/more/wuse/works/661bb3bde2251.srt")
