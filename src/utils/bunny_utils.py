from pathlib import Path
from typing import Optional, Dict, List, Union

import requests


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
        self.headers = {
            "AccessKey": api_key,
            "accept": "application/json"
        }

    def upload_video(self, file_path: Union[str, Path], title: Optional[str] = None) -> Dict:
        """
        Upload a video to Bunny Stream.
        
        Args:
            file_path (Union[str, Path]): Path to the video file
            title (Optional[str]): Title for the video. If None, uses filename
            
        Returns:
            Dict: Response from Bunny.net API containing video details
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Video file not found: {file_path}")

        # Create the video object first
        create_url = f"{self.base_url}/{self.library_id}/videos"
        title = title or file_path.stem

        create_response = requests.post(
            create_url,
            headers=self.headers,
            json={"title": title}
        )
        create_response.raise_for_status()
        video_data = create_response.json()

        # Upload the video file
        upload_url = f"{self.base_url}/{self.library_id}/videos/{video_data['guid']}"

        with open(file_path, "rb") as video_file:
            upload_headers = {**self.headers, "Content-Type": "application/octet-stream"}
            upload_response = requests.put(
                upload_url,
                headers=upload_headers,
                data=video_file
            )
            upload_response.raise_for_status()

        return upload_response.json()

    def upload_subtitle(
            self,
            video_guid: str,
            subtitle_file: Union[str, Path],
            language_code: str,
            label: Optional[str] = None
    ) -> Dict:
        """
        Upload a subtitle file for a specific video.
        
        Args:
            video_guid (str): The GUID of the video
            subtitle_file (Union[str, Path]): Path to the subtitle file (.vtt or .srt)
            language_code (str): ISO 639-1 language code (e.g., 'en', 'es', 'fr')
            label (Optional[str]): Display label for the subtitle track
            
        Returns:
            Dict: Response from Bunny.net API containing subtitle details
        """
        subtitle_path = Path(subtitle_file)
        if not subtitle_path.exists():
            raise FileNotFoundError(f"Subtitle file not found: {subtitle_path}")

        if subtitle_path.suffix.lower() not in ['.vtt', '.srt']:
            raise ValueError("Subtitle file must be .vtt or .srt format")

        url = f"{self.base_url}/{self.library_id}/videos/{video_guid}/captions/{language_code}"

        with open(subtitle_path, "rb") as subtitle_file:
            upload_headers = {**self.headers}
            if label:
                upload_headers["Caption-Label"] = label

            response = requests.post(
                url,
                headers=upload_headers,
                data=subtitle_file
            )
            response.raise_for_status()

        return response.json()

    def list_subtitles(self, video_guid: str) -> List[Dict]:
        """
        List all subtitles for a specific video.
        
        Args:
            video_guid (str): The GUID of the video
            
        Returns:
            List[Dict]: List of subtitle tracks and their details
        """
        url = f"{self.base_url}/{self.library_id}/videos/{video_guid}/captions"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()

        return response.json()

    def delete_subtitle(self, video_guid: str, language_code: str) -> bool:
        """
        Delete a subtitle track for a specific video.
        
        Args:
            video_guid (str): The GUID of the video
            language_code (str): ISO 639-1 language code of the subtitle to delete
            
        Returns:
            bool: True if deletion was successful
        """
        url = f"{self.base_url}/{self.library_id}/videos/{video_guid}/captions/{language_code}"

        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()

        return True


# Example usage:
"""
# Initialize the client
client = BunnyStreamClient(api_key="your-api-key", library_id="your-library-id")

# Upload a video
video_response = client.upload_video("path/to/video.mp4", "My Video Title")
video_guid = video_response["guid"]

# Upload subtitles in different languages
client.upload_subtitle(video_guid, "path/to/english.vtt", "en", "English")
client.upload_subtitle(video_guid, "path/to/spanish.vtt", "es", "Español")
client.upload_subtitle(video_guid, "path/to/french.vtt", "fr", "Français")

# List all subtitles for the video
subtitles = client.list_subtitles(video_guid)
print(f"Available subtitles: {subtitles}")

# Delete a subtitle track if needed
client.delete_subtitle(video_guid, "fr")
"""
