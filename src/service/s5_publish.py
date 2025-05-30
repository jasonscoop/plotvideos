from base64 import b64encode
from typing import Dict, Tuple

import httpx
from sqlalchemy.orm import Session

from src.lib.connection import engine
from src.lib.models import Video
from src.lib.consts import VideoStatus
from src.lib.config import WP_BASE_URL, WP_USERNAME, WP_PASSWORD

# === Configuration ===
API_URL = f"{WP_BASE_URL}/wp-json/wp/v2/posts"
CREDENTIALS = b64encode(f"{WP_USERNAME}:{WP_PASSWORD}".encode()).decode("utf-8")
HEADERS = {
    "Authorization": f"Basic {CREDENTIALS}",
    "Content-Type": "application/json"
}

def create_post(client: httpx.Client, title: str, content: str, lang: str, image_url: str) -> Dict:
    """Create a new WordPress post."""
    data = {
        "title": title,
        "content": content,
        "status": "publish",
        "lang": lang,
        "meta": {
            "_harikrutfiwu_url": image_url,
            "_harikrutfiwu_alt": title
        }
    }
    
    response = client.post(API_URL, json=data, headers=HEADERS)
    response.raise_for_status()
    return response.json()

def link_posts(client: httpx.Client, en_post_id: int, zh_post_id: int) -> Dict:
    """Link English and Chinese posts together."""
    link_data = {
        "posts": {
            "en": en_post_id,
            "zh": zh_post_id
        }
    }
    
    response = client.post(
        f"{WP_BASE_URL}/wp-json/custom/v1/link-posts",
        json=link_data,
        headers=HEADERS
    )
    return response.json()

def publish_video_to_wordpress(video: Video) -> Tuple[bool, str]:
    """Publish a video to WordPress with both English and Chinese versions."""
    try:
        with httpx.Client() as client:
            # Create English post
            en_post = create_post(
                client=client,
                title=f"Video {video.id}",  # You might want to use a better title
                content=video.title,  # You might want to use better content
                lang="en",
                image_url=video.url  # You might want to use a thumbnail URL instead
            )
            print(f"✅ English post created with ID: {en_post['id']}")

            # Create Chinese post
            zh_post = create_post(
                client=client,
                title=f"视频 {video.id}",  # You might want to use a translated title
                content=video.title,  # You might want to use translated content
                lang="zh",
                image_url=video.url  # You might want to use a thumbnail URL instead
            )
            print(f"✅ Chinese post created with ID: {zh_post['id']}")

            # Link the posts
            link_result = link_posts(client, en_post["id"], zh_post["id"])
            print("✅ Posts linked:", link_result)
            
            return True, ""
    except Exception as e:
        return False, str(e)

def process_pending_videos():
    """Process all videos with subtitle_translated status."""
    with Session(engine) as session:
        pending_videos = session.query(Video).filter(
            Video.status == VideoStatus.subtitle_translated
        ).all()
        
        for video in pending_videos:
            success, error = publish_video_to_wordpress(video)
            if success:
                video.status = VideoStatus.published
                print(f"Successfully published video {video.id}")
            else:
                video.status = VideoStatus.publish_failed
                video.failed_reason = error
                print(f"Failed to publish video {video.id}: {error}")
            
            session.commit()

if __name__ == "__main__":
    process_pending_videos()

