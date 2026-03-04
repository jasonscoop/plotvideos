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
    Transcode a video into multi-resolution HLS (H.264 / AAC) in a single
    ffmpeg invocation using filter_complex (one decode, three encodes).

    Returns the path to the master playlist (master.m3u8).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for r in HLS_RENDITIONS:
        (output_dir / r["name"]).mkdir(parents=True, exist_ok=True)

    n = len(HLS_RENDITIONS)

    # Build filter_complex: split input once, scale each branch
    filter_parts = [f"[0:v]split={n}" + "".join(f"[vin{i}]" for i in range(n))]
    for i, r in enumerate(HLS_RENDITIONS):
        filter_parts.append(f"[vin{i}]scale=-2:{r['height']}[v{i}]")
    filter_complex = ";".join(filter_parts)

    command = [
        "ffmpeg", "-y",
        "-i", str(video_path),
        "-filter_complex", filter_complex,
    ]

    for i, r in enumerate(HLS_RENDITIONS):
        seg = output_dir / r["name"] / "segment_%03d.ts"
        playlist = output_dir / r["name"] / "index.m3u8"
        command += [
            "-map", f"[v{i}]", "-map", "0:a",
            "-c:v", "libx264", "-profile:v", "high", "-preset", "veryfast",
            "-b:v", r["video_bitrate"],
            "-c:a", "aac", "-ac", "2", "-b:a", r["audio_bitrate"],
            "-f", "hls",
            "-hls_time", "6",
            "-hls_playlist_type", "vod",
            "-hls_segment_filename", str(seg),
            str(playlist),
        ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    master_lines = ["#EXTM3U", "#EXT-X-VERSION:3"]
    for r in HLS_RENDITIONS:
        master_lines.append(
            f"#EXT-X-STREAM-INF:BANDWIDTH={r['bandwidth']},RESOLUTION={r['resolution']}"
        )
        master_lines.append(f"{r['name']}/index.m3u8")

    master_path = output_dir / "master.m3u8"
    master_path.write_text("\n".join(master_lines) + "\n")
    return master_path
