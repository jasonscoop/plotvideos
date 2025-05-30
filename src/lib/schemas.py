from src.lib.config import VIDEOS_DIR


class StorePath:
    def __init__(self, host: str, original_id: str):
        parent_dir = f"{host}/{original_id[0:2]}/{original_id}"
        self.parent = VIDEOS_DIR / parent_dir
        self.vtt = self.parent / "subtitle.vtt",
        self.translated_vtts = self.parent / "subtitles",
        self.azure_results = self.parent / "azure-results.json",
        self.wav = self.parent / "audio.wav"
