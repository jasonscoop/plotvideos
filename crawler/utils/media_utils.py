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
    {"idx": 0, "name": "480p",  "bitrate": "1500k", "size": "854x480",  "bandwidth": 1_500_000},
    {"idx": 1, "name": "720p",  "bitrate": "3000k", "size": "1280x720", "bandwidth": 3_000_000},
    {"idx": 2, "name": "1080p", "bitrate": "5000k", "size": "1920x1080","bandwidth": 5_000_000},
]


def generate_hls(video_path: Path, output_dir: Path) -> Path:
    """
    Transcode a video into multi-resolution HLS (H.264 / AAC, fMP4 segments)
    using ffmpeg's built-in variant stream support and master playlist generation.

    Returns the path to the master playlist (master.m3u8).
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    for r in HLS_RENDITIONS:
        (output_dir / r["name"]).mkdir(parents=True, exist_ok=True)

    stream_map = " ".join(f"v:{r['idx']},a:{r['idx']}" for r in HLS_RENDITIONS)

    command = [
        "ffmpeg", "-y",
        "-i", str(video_path),
    ]

    # Map video + audio once per rendition
    for r in HLS_RENDITIONS:
        command += ["-map", "0:v", "-map", "0:a"]

    # Per-rendition video bitrate & resolution
    for r in HLS_RENDITIONS:
        command += [
            f"-b:v:{r['idx']}", r["bitrate"],
            f"-s:v:{r['idx']}", r["size"],
        ]

    # Shared encode settings
    command += [
        "-c:v", "libx264", "-preset", "veryfast",
        "-g", "48", "-keyint_min", "48", "-sc_threshold", "0",
        "-c:a", "aac", "-ac", "2", "-b:a", "128k",
        "-f", "hls",
        "-hls_time", "6",
        "-hls_playlist_type", "vod",
        "-hls_segment_type", "fmp4",
        "-master_pl_name", "master.m3u8",
        "-var_stream_map", stream_map,
        str(output_dir / "%v/prog_index.m3u8"),
    ]

    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

    # ffmpeg names variant dirs 0, 1, 2 — rename to 480p, 720p, 1080p
    for r in HLS_RENDITIONS:
        src = output_dir / str(r["idx"])
        dst = output_dir / r["name"]
        if src.exists() and src != dst:
            if dst.exists():
                import shutil
                shutil.rmtree(dst)
            src.rename(dst)

    # Rewrite master playlist with friendly directory names
    master_path = output_dir / "master.m3u8"
    if master_path.exists():
        content = master_path.read_text()
        for r in HLS_RENDITIONS:
            content = content.replace(f"{r['idx']}/prog_index.m3u8", f"{r['name']}/prog_index.m3u8")
        master_path.write_text(content)

    return master_path
