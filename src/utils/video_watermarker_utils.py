import os
from pathlib import Path

import cv2
import ffmpeg
import pytesseract
from PIL import Image


class WatermakerUtils:
    def __init__(self, video_path: Path, logo: str):
        self.logo = logo
        self.video_path: Path = video_path
        self.keyframes_path: Path = self.video_path.parent / "_keyframes" / video_path.stem

    def has_watermark(self) -> bool:
        self.extract_video_keyframes()
        content = self.extract_video_texts()
        return self.logo in content

    def extract_video_keyframes(self):
        os.makedirs(self.keyframes_path, exist_ok=True)
        (
            ffmpeg
            .input(self.video_path)
            .output(
                os.path.join(self.keyframes_path, 'frame_%04d.jpg'),
                vf='select=eq(pict_type\\,I)',
                vsync='vfr',
                qscale=2
            )
            .run()
        )

    def preprocess_image(self, path: Path) -> Image.Image:
        img = cv2.imread(str(path))
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.medianBlur(gray, 3)
        thresh = cv2.adaptiveThreshold(blur, 255,
                                       cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY, 11, 2)
        return Image.fromarray(thresh)

    def extract_video_texts(self) -> str:
        texts = []
        for fname in os.listdir(self.keyframes_path):
            if not fname.endswith(".jpg"):
                continue

            path = self.keyframes_path / fname
            preprocessed = self.preprocess_image(path)
            texts.append(pytesseract.image_to_string(preprocessed, config='--psm 6'))

        return "\n".join(texts)
