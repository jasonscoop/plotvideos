import csv
import json
import re
from pathlib import Path

import pymysql
from loguru import logger

from src.lib.config import WORKS_DIR
from src.lib.consts import WEBSITES

# MySQL connection settings
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "12345678"
DB_NAME = "wordpress2"
TABLE_PREFIX = "wp_"  # Change if your WordPress table prefix is different

CSV_FILE = WORKS_DIR / "videos_rows.csv"


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


def generate_video_html(short_name, filename, available_langs):
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

    # Always use default thumbnail URL (no download/upload)
    thumb_url = f"https://play.luckvideos.com/{path_prefix}/thumbnail.jpg"

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
    mapping = {}
    with open(CSV_FILE, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            host = row["host"]
            filename = row["filename"]
            library_id = row["bunny_library_id"]
            video_id = row["bunny_video_id"]

            website_info = WEBSITES.get(host)
            if website_info is None:
                logger.error(f"⚠️ Unknown host {host}")
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
                website_info[0],
                filename,
                available_langs,
            )
    return mapping


def main():
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
            logger.error(f"⚠️ No CSV mapping for {library_id} {video_id}")
            continue

        short_name, filename, available_langs, _ = mapping[key]

        # Build HTML and default thumbnail URL without any download/upload
        video_html, thumb_url = generate_video_html(
            short_name, filename, available_langs
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
