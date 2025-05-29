# 🎥 Short Video Pipeline Doc: RapidAPI + yt-dlp + Redis + Celery

## Overview

Automated pipeline to:
- Fetch videos via RapidAPI
- Download with yt-dlp
- Remove start ad clip and recognize watermarker
- Generate subtitles with azure api
- Translate title and subtitles
- Publish to MediaCMS

