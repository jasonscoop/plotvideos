import os
import re
import subprocess
from pathlib import Path

import ffmpeg
import pytesseract
from PIL import Image


class VideoUtils:
    @staticmethod
    def detect_scene_change(video_path, scene_threshold=0.4):
        # Build the ffmpeg command using ffmpeg-python
        stream = ffmpeg.input(video_path)
        stream = stream.video.filter('select', f'gt(scene,{scene_threshold})').filter('showinfo')
        cmd = ffmpeg.output(stream, 'null', f='null').compile()

        # Run the command and capture stderr (scene change info is printed to stderr)
        result = subprocess.run(cmd, stderr=subprocess.PIPE, text=True)

        # Extract frame timestamps from ffmpeg showinfo output
        matches = re.findall(r'pts_time:(\d+\.\d+)', result.stderr)
        if matches:
            return float(matches[0])  # First major scene change time
        return 0.0

    @staticmethod
    def trim_video(input_path, output_path, start_time):
        ffmpeg.input(input_path, ss=start_time).output(output_path, c='copy').run()