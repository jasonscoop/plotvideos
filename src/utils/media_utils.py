import subprocess
from pathlib import Path

from tenacity import retry, stop_after_attempt, wait_fixed


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
