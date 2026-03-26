#!/bin/sh
set -e
# Upgrade yt-dlp in the synced venv before crawler/api start (set YTDLP_SKIP_AUTO_UPGRADE=1 to skip).
if [ "${YTDLP_SKIP_AUTO_UPGRADE:-0}" != "1" ]; then
  uv pip install --python /workspace/.venv/bin/python -U yt-dlp
fi
exec "$@"
