import base64
from pathlib import Path

import requests
from loguru import logger
from tenacity import stop_after_attempt, retry, wait_fixed

from src.lib.consts import WEBSITES
from src.lib.models import Video, Language
from src.utils.vtt_utils import correct_vtt, is_valid_vtt


class BunnyStreamClient:
    def __init__(self, api_key: str, library_id: str):
        """
        Initialize the Bunny Stream client.
        
        Args:
            api_key (str): Your Bunny.net API key
            library_id (str): Your Bunny Stream library ID
        """
        self.api_key = api_key
        self.library_id = library_id
        self.base_url = "https://video.bunnycdn.com/library"
        self.headers = {"AccessKey": api_key, "accept": "application/json"}
        self.video_headers = {**self.headers, "Content-Type": "application/octet-stream"}
        self.vtt_headers = {**self.headers, "Content-Type": "text/vtt"}

    @staticmethod
    def stream_video_file(path: Path, chunk_size: int = 1024 * 1024):  # 1MB chunks
        with open(path, "rb") as f:
            while chunk := f.read(chunk_size):
                yield chunk

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(3), reraise=True)
    def upload_video(self, video: Video) -> str:
        video_path = video.path.video
        if not video_path.exists():
            raise FileNotFoundError(f"[{video.id}] Video file not found: {video_path}")

        create_url = f"{self.base_url}/{self.library_id}/videos"
        create_response = requests.post(
            create_url,
            headers=self.headers,
            json={
                "title": video.title or video_path.stem,
                "collectionId": WEBSITES[video.host]["bunny_collection_id"]
            }
        )
        create_response.raise_for_status()
        video_data = create_response.json()

        upload_url = f"{self.base_url}/{self.library_id}/videos/{video_data['guid']}"
        upload_response = requests.put(upload_url,
                                       headers=self.video_headers,
                                       data=self.stream_video_file(video_path))
        upload_response.raise_for_status()

        return video_data["guid"]

    @retry(wait=wait_fixed(1), stop=stop_after_attempt(3), reraise=True)
    def upload_subtitle(
            self,
            video_guid: str,
            vtt_path: Path,
            lang: Language,
    ):
        vtt_path = Path(vtt_path)
        if not vtt_path.exists():
            logger.error(f"[{video_guid}] Video file not found: {vtt_path}")
            return

        vtt_content = vtt_path.read_text()
        if not vtt_content or vtt_content.strip() == "WEBVTT":
            logger.error(f"[{video_guid}] vtt content is empty '{lang.code}']'")
            return

        if not is_valid_vtt(vtt_content):
            vtt_content = correct_vtt(vtt_content)
            logger.warning(f"[{video_guid}] Corrected vtt content '{lang.code}'")

        url = f"{self.base_url}/{self.library_id}/videos/{video_guid}/captions/{lang.code}"
        payload = {
            "srclang": lang.code,
            "label": lang.native_name,
            "captionsFile": base64.b64encode(vtt_content.encode("utf-8")).decode("utf-8")
        }
        response = requests.post(url, headers=self.headers, json=payload)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 400:
                logger.error(f"[{video_guid}] [{lang.code}] error: {response.text}")

        # save back to disk for uploading to s3
        vtt_path.write_text(vtt_content)
