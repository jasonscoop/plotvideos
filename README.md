# 🎥 Short Video Pipeline Doc: RapidAPI + yt-dlp + Redis + Celery

## Overview

Automated pipeline to:

- Fetch videos via RapidAPI
- Download with yt-dlp
- Remove start ad clip and recognize watermarker
- Generate subtitles with azure api
- Translate title and subtitles
- Publish to MediaCMS

```shell
docker compose up --build --no-deps -e  LT_LOAD_ONLY=en,zh,hi,es,ar,fr,bn,pt,ru,ur,id,de,ja,sw
docker build -f ./docker/Dockerfile --build-arg models="en,zh,hi,es,ar,fr,bn,pt,ru,ur,id,de,ja,sw" .
./run.sh --load_only_lang_codes en,zh,hi,es,ar,fr,bn,pt,ru,ur,id,de,ja,sw
```

# Hosts

- https://www.hostinger.com/pricing?content=vps-hosting
- https://www.kamatera.com/pricing/
- https://contabo.com/en/vps/cloud-vps-10/?image=ubuntu.332&qty=1&contract=12&storage-type=cloud-vps-10-150-gb-ssd