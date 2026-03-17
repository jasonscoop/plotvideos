import json
import platform
import shutil
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


ALL_RENDITIONS = [
    {"name": "480p",  "height": 480,  "bitrate": "1500k", "size": "854x480",  "bandwidth": 1_500_000},
    {"name": "720p",  "height": 720,  "bitrate": "3000k", "size": "1280x720", "bandwidth": 3_000_000},
    {"name": "1080p", "height": 1080, "bitrate": "5000k", "size": "1920x1080","bandwidth": 5_000_000},
]


def _get_video_height(video_path: Path) -> int:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=height", "-of", "json", str(video_path)],
        capture_output=True, text=True, check=True,
    )
    streams = json.loads(result.stdout).get("streams", [])
    return streams[0]["height"] if streams else 0


def generate_hls(video_path: Path, output_dir: Path) -> Path:
    src_height = _get_video_height(video_path)

    # Only keep renditions <= source height; always keep at least the smallest
    renditions = [r for r in ALL_RENDITIONS if r["height"] <= src_height]
    if not renditions:
        renditions = [ALL_RENDITIONS[0]]

    # Assign sequential indices
    for i, r in enumerate(renditions):
        r["idx"] = i

    output_dir.mkdir(parents=True, exist_ok=True)

    stream_map = " ".join(f"v:{r['idx']},a:{r['idx']}" for r in renditions)

    command = ["ffmpeg", "-y", "-i", str(video_path)]

    for _ in renditions:
        command += ["-map", "0:v", "-map", "0:a"]

    for r in renditions:
        command += [
            f"-b:v:{r['idx']}", r["bitrate"],
            f"-s:v:{r['idx']}", r["size"],
        ]

    if platform.system() == "Darwin":
        command += ["-c:v", "h264_videotoolbox", "-allow_sw", "1"]
    else:
        command += ["-c:v", "libx264", "-preset", "veryfast"]

    command += [
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

    # Rename numbered dirs (0, 1, 2) to friendly names (480p, 720p, 1080p)
    for r in renditions:
        src = output_dir / str(r["idx"])
        dst = output_dir / r["name"]
        if src.exists() and src != dst:
            if dst.exists():
                shutil.rmtree(dst)
            src.rename(dst)

    # Rewrite master playlist with friendly directory names
    master_path = output_dir / "master.m3u8"
    if master_path.exists():
        content = master_path.read_text()
        for r in renditions:
            content = content.replace(f"{r['idx']}/prog_index.m3u8", f"{r['name']}/prog_index.m3u8")
        master_path.write_text(content)

    return master_path
