# Crawler (Python)

Video pipeline: scheduler, FastAPI, yt-dlp, storage.

Layout:

- `src/core/`, `src/crud/`, `src/service/`, `src/utils/` — packages
- `src/api.py`, `src/scheduler.py` — entry modules

Run from this directory (`PYTHONPATH=src` or installed venv): `python -m scheduler`, `uvicorn api:app`.

Docker: `docker compose` from repo root uses `crawler/docker-compose.yml`.
