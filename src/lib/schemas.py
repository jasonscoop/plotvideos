from pathlib import Path

from pydantic import BaseModel

from src.lib.config import VIDEOS_DIR


class StorePath(BaseModel):
    parent: Path
    vtt: Path
    translated_vtts: Path
    azure_results: Path
    wav: Path

    @classmethod
    def generate(cls, host: str, original_id: str) -> "StorePath":
        parent_dir = f"{host}/{original_id[0:2]}/{original_id}"
        parent = VIDEOS_DIR / parent_dir

        return StorePath(
            parent=parent,
            vtt=parent / "subtitle.vtt",
            translated_vtts=parent / "subtitles",
            azure_results=parent / "azure-results.json",
            wav=parent / "audio.wav"
        )
