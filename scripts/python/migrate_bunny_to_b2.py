import csv
import json
import os
import re
import tempfile
from pathlib import Path

import pymysql
import yt_dlp
import requests
from b2sdk.v2 import B2Api, InMemoryAccountInfo
from dotenv import load_dotenv

# MySQL connection settings
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "12345678"
DB_NAME = "wordpress2"
TABLE_PREFIX = "wp_"  # Change if your WordPress table prefix is different

load_dotenv()

# B2 settings - Load from environment variables
B2_APPLICATION_KEY_ID = os.getenv("B2_APPLICATION_KEY_ID")
B2_APPLICATION_KEY = os.getenv("B2_APPLICATION_KEY")
B2_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")

CSV_FILE = "/Users/garymeng/Downloads/videos_rows.csv"

WEBSITES = {
    "www.pornhub.com": "ph",
    "www.xhamster.com": "xh",
    "www.xvideos.com": "xv",
    "www.eporner.com": "ep",
    "www.youjizz.com": "yj",
    "www.redtube.com": "rt",
    "www.youporn.com": "yp",
    "www.pornhd.com": "pd",
    "spankbang.com": "sb",
    "www.youtube.com": "yt",
}

LANGUAGE_NAMES = {
    "zh": "中文",
    "hi": "हिन्दी",
    "es": "Español",
    "ar": "العربية",
    "fr": "Français",
    "bn": "বাংলা",
    "pt": "Português",
    "ru": "Русский",
    "ur": "اردو",
    "id": "Bahasa Indonesia",
    "de": "Deutsch",
    "ja": "日本語",
    "sw": "Kiswahili",
    "en": "English",
    "tr": "Türkçe",
}


class B2Client:
    def __init__(self, key_id: str, application_key: str, bucket_name: str):
        self.info = InMemoryAccountInfo()
        self.api = B2Api(self.info)
        self.api.authorize_account("production", key_id, application_key)
        self.bucket = self.api.get_bucket_by_name(bucket_name)

    def upload_file(self, file_path: Path, b2_key: str) -> str:
        """Upload a file to B2 and return the public URL"""
        uploaded_file = self.bucket.upload_local_file(
            local_file=str(file_path), file_name=b2_key
        )
        return f"https://f004.backblazeb2.com/file/{self.bucket.name}/{b2_key}"


def download_thumbnail(url: str, output_path: Path) -> bool:
    """Download thumbnail using yt-dlp"""
    ydl_opts = {
        "writethumbnail": True,
        "outtmpl": str(output_path.with_suffix("")),
        "skip_download": True,  # Skip downloading video/audio
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "proxy": "socks5://127.0.0.1:9150",  # Tor proxy
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first to check if thumbnail is available
            info = ydl.extract_info(url, download=False)
            if not info:
                print(f"No info extracted for {url}")
                return False

            # Download the video info (this will also download thumbnail)
            ydl.download([url])

        # yt-dlp might save with different extensions, find the thumbnail file
        for ext in [".webp", ".jpg", ".jpeg", ".png"]:
            thumb_file = output_path.with_suffix(ext)
            if thumb_file.exists():
                print(f"Found thumbnail: {thumb_file}")
                return True

        # If no thumbnail found, try to get it from the info
        if "thumbnail" in info:
            try:
                response = requests.get(info["thumbnail"], timeout=10)
                if response.status_code == 200:
                    output_path.with_suffix(".webp").write_bytes(response.content)
                    print(f"Downloaded thumbnail from info: {info['thumbnail']}")
                    return True
            except Exception as e:
                print(f"Failed to download thumbnail from info: {e}")

        return False
    except Exception as e:
        print(f"Error downloading thumbnail for {url}: {e}")
        return False


def generate_video_html(short_name, filename, available_langs, thumbnail_url=None):
    """
    Generate HTML video tag with only available subtitle tracks, English first.
    """
    name = Path(filename).stem
    path_prefix = f"{short_name}/{name[:2]}/{name}"
    mp4_url = f"https://play.luckvideos.com/{path_prefix}/{filename}"

    # Sort: English first (if present), then others
    sorted_langs = []
    if "en" in available_langs:
        sorted_langs.append("en")
    sorted_langs.extend([lang for lang in available_langs if lang != "en"])

    tracks_html = []
    for lang in sorted_langs:
        native_name = LANGUAGE_NAMES.get(lang, lang)
        track_url = f"https://play.luckvideos.com/{path_prefix}/subtitles/{lang}.vtt"
        default_attr = " default" if lang == "en" else ""
        tracks_html.append(
            f'<track kind="subtitles" src="{track_url}" srclang="{lang}" label="{native_name}"{default_attr}>'
        )

    # Use provided thumbnail URL or fallback to default
    thumb_url = thumbnail_url or f"https://play.luckvideos.com/thumbnail.jpg"

    return (
        f"""
<video controls src="{mp4_url}" preload="metadata" crossorigin="anonymous">
    {'\n    '.join(tracks_html)}
    Your browser does not support the video tag.
</video>
""".strip(),
        thumb_url,
    )


def load_csv_mapping():
    """
    Load CSV into dict mapping (library_id, video_id) -> (short_name, filename, available_langs, url)
    """
    mapping = {}
    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            host = row["host"]
            filename = row["filename"]
            library_id = row["bunny_library_id"]
            video_id = row["bunny_video_id"]
            url = row["url"]

            short_name = WEBSITES.get(host)
            if not short_name:
                continue

            try:
                title_translations = json.loads(row["title_translations"])
                # Handle both dict and list cases
                if isinstance(title_translations, dict):
                    available_langs = [
                        lang
                        for lang in title_translations.keys()
                        if lang in LANGUAGE_NAMES
                    ]
                elif isinstance(title_translations, list):
                    # If it's a list of dicts, extract language codes from dict keys
                    available_langs = []
                    for item in title_translations:
                        if isinstance(item, dict):
                            available_langs.extend(
                                [lang for lang in item.keys() if lang in LANGUAGE_NAMES]
                            )
                        elif isinstance(item, str) and item in LANGUAGE_NAMES:
                            available_langs.append(item)
                    # Remove duplicates while preserving order
                    available_langs = list(dict.fromkeys(available_langs))
                else:
                    available_langs = []
            except json.JSONDecodeError:
                available_langs = []

            mapping[(library_id, video_id)] = (
                short_name,
                filename,
                available_langs,
                url,
            )
    return mapping


def main():
    # Validate B2 settings
    if not all([B2_APPLICATION_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_NAME]):
        print("❌ B2 settings not configured!")
        print("Please set the following environment variables:")
        print("  - B2_APPLICATION_KEY_ID")
        print("  - B2_APPLICATION_KEY")
        print("  - B2_BUCKET_NAME")
        print("\nOr run: python scripts/python/setup_b2_config.py")
        return

    # Initialize B2 client
    b2_client = B2Client(B2_APPLICATION_KEY_ID, B2_APPLICATION_KEY, B2_BUCKET_NAME)

    mapping = load_csv_mapping()

    conn = pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
    )
    cursor = conn.cursor()

    # Find posts with BunnyCDN iframe embeds
    cursor.execute(
        f"""
        SELECT ID, post_content 
        FROM {TABLE_PREFIX}posts 
        WHERE post_content LIKE '%iframe.mediadelivery.net/embed/%'
    """
    )
    rows = cursor.fetchall()

    for post_id, content in rows:
        m = re.search(r"/embed/(\d+)/([a-f0-9-]+)\?", content)
        if not m:
            continue

        library_id, video_id = m.groups()
        key = (library_id, video_id)
        if key not in mapping:
            print(f"⚠️ No CSV mapping for {library_id} {video_id}")
            continue

        short_name, filename, available_langs, url = mapping[key]
        if not available_langs:
            print(f"⚠️ No languages in title_translations for {library_id} {video_id}")
            continue

        # Download and upload thumbnail
        thumbnail_url = None
        if url:
            print(f"📥 Downloading thumbnail for {url}")
            with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp_file:
                tmp_path = Path(tmp_file.name)

            if download_thumbnail(url, tmp_path):
                # Generate B2 key for thumbnail
                name = Path(filename).stem
                b2_key = f"thumbnails/{short_name}/{name[:2]}/{name}/thumbnail.webp"

                print(f"📤 Uploading thumbnail to B2: {b2_key}")
                try:
                    thumbnail_url = b2_client.upload_file(tmp_path, b2_key)
                    print(f"✅ Thumbnail uploaded: {thumbnail_url}")
                except Exception as e:
                    print(f"❌ Failed to upload thumbnail: {e}")
                    thumbnail_url = None
                finally:
                    # Clean up temp file
                    tmp_path.unlink(missing_ok=True)
            else:
                print(f"❌ Failed to download thumbnail for {url}")

        video_html, thumb_url = generate_video_html(
            short_name, filename, available_langs, thumbnail_url
        )

        # Update post content
        cursor.execute(
            f"UPDATE {TABLE_PREFIX}posts SET post_content = %s WHERE ID = %s",
            (video_html, post_id),
        )

        # Update thumbnail meta
        cursor.execute(
            f"""
            UPDATE {TABLE_PREFIX}postmeta 
            SET meta_value = %s 
            WHERE post_id = %s AND meta_key = '_harikrutfiwu_url'
            """,
            (thumb_url, post_id),
        )

        print(f"✅ Updated post {post_id} with new video & thumbnail")

    conn.commit()
    cursor.close()
    conn.close()


if __name__ == "__main__":
    main()
