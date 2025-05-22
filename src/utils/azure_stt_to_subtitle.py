import azure.cognitiveservices.speech as speechsdk
import json
import datetime
import os
from pydub import AudioSegment
import time
from pathlib import Path
import re

from src.lib.config import AZURE_SPEECH_REGION, AZURE_SPEECH_KEY


def split_long_text(text, max_length=50):
    """
    Split long text into shorter segments at natural break points.
    """
    if len(text) <= max_length:
        return [text]
    
    # Define break points (punctuation marks and conjunctions)
    break_points = ['. ', '? ', '! ', ', ', '; ', ' and ', ' but ', ' or ', ' so ']
    
    segments = []
    while len(text) > max_length:
        # Find the last break point before max_length
        best_break = -1
        for delimiter in break_points:
            pos = text[:max_length + len(delimiter)].rfind(delimiter)
            if pos > best_break:
                best_break = pos
        
        if best_break == -1:
            # If no break point found, break at the last space before max_length
            best_break = text[:max_length].rfind(' ')
            if best_break == -1:
                # If no space found, force break at max_length
                best_break = max_length
        
        # Add segment and continue with remaining text
        segment = text[:best_break].strip()
        if segment:
            segments.append(segment)
        text = text[best_break:].strip()
    
    if text:
        segments.append(text)
    
    return segments


def convert_to_wav(input_path, target_sample_rate=16000):
    """
    Convert audio file to WAV format optimized for speech recognition.
    """
    print(f"Converting audio file to WAV format...")
    start_time = time.time()
    
    # Load audio file
    audio = AudioSegment.from_file(input_path)
    duration = len(audio) / 1000.0  # Duration in seconds
    
    # Optimize for speech recognition:
    # 1. Convert to mono
    # 2. Set sample rate to 16kHz
    # 3. Normalize volume
    audio = audio.set_channels(1).set_frame_rate(target_sample_rate).normalize()
    
    # Create a temporary WAV file
    wav_path = os.path.join(
        os.path.dirname(input_path),
        f"{Path(input_path).stem}_temp.wav"
    )
    
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
    
    print(f"Audio conversion completed in {time.time() - start_time:.2f} seconds")
    print(f"Audio duration: {duration:.2f} seconds")
    
    return wav_path, duration


def audio_to_srt(audio_path, output_path):
    start_time = time.time()
    
    try:
        # Convert to WAV first
        wav_path, duration = convert_to_wav(audio_path)
        
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
        last_progress = 0
        processed_duration = 0

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

                    # Split long text into segments
                    segments = split_long_text(text)
                    word_count = len(words)
                    
                    if len(segments) == 1:
                        # Single segment - use the full timing
                        start = float(words[0]["Offset"]) / 10_000_000
                        end = (float(words[-1]["Offset"]) + float(words[-1]["Duration"])) / 10_000_000
                        entry = f"{counter}\n{format_time(start)} --> {format_time(end)}\n{text}\n"
                        entries.append(entry)
                        counter += 1
                    else:
                        # Multiple segments - distribute timing proportionally
                        total_chars = sum(len(s) for s in segments)
                        total_duration = (float(words[-1]["Offset"]) + float(words[-1]["Duration"]) - float(words[0]["Offset"])) / 10_000_000
                        start_time = float(words[0]["Offset"]) / 10_000_000
                        
                        for segment in segments:
                            segment_duration = (len(segment) / total_chars) * total_duration
                            end_time = start_time + segment_duration
                            
                            entry = f"{counter}\n{format_time(start_time)} --> {format_time(end_time)}\n{segment}\n"
                            entries.append(entry)
                            counter += 1
                            start_time = end_time

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

    finally:
        # Clean up temporary WAV file
        try:
            if 'wav_path' in locals():
                os.unlink(wav_path)
                print("Temporary WAV file cleaned up")
        except Exception as e:
            print(f"Warning: Could not delete temporary file {wav_path}: {e}")


if __name__ == '__main__':
    audio_to_srt("/Users/garymeng/code/more/wuse/works/661bb3bde2251.mp3", "/Users/garymeng/code/more/wuse/works/661bb3bde2251.srt")