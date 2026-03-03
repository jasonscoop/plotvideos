import re
import subprocess
from pathlib import Path

import ffmpeg


class StartAdTrimmer:
    def __init__(self, video_path: Path):
        self.video_path: Path = video_path
        self.new_video_path: Path = video_path.parent / f"{video_path.stem}_trimmed{video_path.suffix}"

    def trim_ad(self) -> Path:
        start = self.detect_scene_change()
        if start != 0.0:
            self.trim_video(start)
            return self.new_video_path

        return self.video_path

    def detect_scene_change(self, scene_threshold=0.4):
        # Build the ffmpeg command using ffmpeg-python
        stream = ffmpeg.input(self.video_path)
        stream = stream.video.filter('select', f'gt(scene,{scene_threshold})').filter('showinfo')
        cmd = ffmpeg.output(stream, 'null', f='null').compile()

        # Run the command and capture stderr (scene change info is printed to stderr)
        result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)

        # Extract frame timestamps from ffmpeg showinfo output
        matches = re.findall(r'pts_time:(\d+\.\d+)', result.stderr)
        if matches:
            return float(matches[0])  # First major scene change time
        return 0.0

    def trim_video(self, start_time):
        ffmpeg.input(self.video_path.as_posix(), ss=start_time).output(self.new_video_path.as_posix(), c='copy').run()
