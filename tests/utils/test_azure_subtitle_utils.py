from pathlib import Path

from src.utils.azure_subtitle_utils import generate_subtitle


def test_create_subtitle():
    generate_subtitle(Path("/Users/garymeng/code/more/wuse/works/videos/661bb3bde2251-small.mp4"))
