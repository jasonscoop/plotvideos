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


HLS_RENDITIONS = [
    {"name": "480p",  "height": 480,  "video_bitrate": "800k",  "audio_bitrate": "96k",  "bandwidth": 800_000,  "resolution": "854x480"},
    {"name": "720p",  "height": 720,  "video_bitrate": "2800k", "audio_bitrate": "128k", "bandwidth": 2_800_000, "resolution": "1280x720"},
    {"name": "1080p", "height": 1080, "video_bitrate": "5000k", "audio_bitrate": "192k", "bandwidth": 5_000_000, "resolution": "1920x1080"},
]


def generate_hls(video_path: Path, output_dir: Path) -> Path:
    """
    Transcode a video into multi-resolution HLS (H.264 / AAC).

    Returns the path to the master playlist (master.m3u8).

    Layout:
      output_dir/
        master.m3u8
        480p/index.m3u8  + segment_*.ts
        720p/index.m3u8  + segment_*.ts
        1080p/index.m3u8 + segment_*.ts
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    master_lines = ["#EXTM3U", "#EXT-X-VERSION:3"]

    for r in HLS_RENDITIONS:
        variant_dir = output_dir / r["name"]
        variant_dir.mkdir(parents=True, exist_ok=True)

        playlist = variant_dir / "index.m3u8"
        segment_pattern = variant_dir / "segment_%03d.ts"

        command = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", f"scale=-2:{r['height']}",
            "-c:v", "libx264", "-profile:v", "high", "-preset", "veryfast",
            "-b:v", r["video_bitrate"],
            "-c:a", "aac", "-ac", "2", "-b:a", r["audio_bitrate"],
            "-f", "hls",
            "-hls_time", "6",
            "-hls_playlist_type", "vod",
            "-hls_segment_filename", str(segment_pattern),
            str(playlist),
        ]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

        master_lines.append(
            f"#EXT-X-STREAM-INF:BANDWIDTH={r['bandwidth']},RESOLUTION={r['resolution']}"
        )
        master_lines.append(f"{r['name']}/index.m3u8")

    master_path = output_dir / "master.m3u8"
    master_path.write_text("\n".join(master_lines) + "\n")
    return master_path
