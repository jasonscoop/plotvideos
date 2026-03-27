# 🎥 Short Video Pipeline Doc: RapidAPI + yt-dlp + Redis + Celery

## Overview

Automated pipeline to:

- Fetch videos via RapidAPI
- Download with yt-dlp
- Remove start ad clip and recognize watermarker
- Generate subtitles with azure api
- Translate title and subtitles
- Publish to MediaCMS

# Hosts

- https://www.hostinger.com/pricing?content=vps-hosting
- https://www.kamatera.com/pricing/
- https://contabo.com/en/vps/cloud-vps-10/?image=ubuntu.332&qty=1&contract=12&storage-type=cloud-vps-10-150-gb-ssd

# Translators

- https://rapidapi.com/IRCTCAPI/api/google-translator9
- https://rapidapi.com/robust-api-robust-api-default/api/google-translate113

# Errors

## Add public access

```sql
CREATE POLICY "Allow public access"
    ON "public"."videos"
    FOR SELECT
    TO anon
    USING (
        (status = 'uploaded'::videostatus)
        );
```

Run with docker

```bash
docker build -t wuse -f crawler/Dockerfile crawler
```

yt-dlp download image:
```bash
yt-dlp -j --proxy "socks5://127.0.0.1:9150"  https://xhamster.com/videos/would-you-like-us-to-suck-you-off-grandpa-serina-gomez-and-mia-trejsi-for-oldhans-xhJOEen > info.json
```

Prevent MacOS sleep while run python:

```bash
caffeinate -i python3 my_script.py
```