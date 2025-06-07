from pathlib import Path
from typing import List, Dict

from pydantic import BaseModel

from src.lib.config import VIDEOS_DIR
from src.lib.consts import WEBSITES
from src.lib.enums import TermType


class StorePath:
    def __init__(self, host: str, original_id: str):
        prefix = f"{WEBSITES[host]['short_name']}/{original_id[0:2]}/{original_id}"
        self.prefix: str = prefix
        self.parent: Path = VIDEOS_DIR / prefix
        self.vtt: Path = self.parent / "subtitle.vtt"
        self.translated_vtts: Path = self.parent / "subtitles"
        self.azure_results: Path = self.parent / "azure-results.json"
        self.wav: Path = self.parent / "audio.wav"


class PreDetectResult(BaseModel):
    text: str
    lang: str
    speech_seconds: float
    total_seconds: float
    speech_ratio: float


class TaxonomyIn(BaseModel):
    taxonomy: TermType
    translations: Dict[str, List[str]]
