# Crawler (Python)

Pipeline: fetch → download → convert → subtitles → translate → HLS → upload. FastAPI (`api`) for the player; storage on B2. Code lives under `src/`; entrypoints are `main` (CLI), `scheduler`, and `api`.

## Configuration

`.env` in this directory. Required: **`DB_URL`**, **`RAPIDAPI_KEY`** (not required if `SKIP_STAGES` includes `s1_fetch`). See `src/core/config.py` for the rest.

## Local

From `crawler/` after `uv sync`:

```bash
export PYTHONPATH=src
python -m main pipeline --runner=s2_download
python -m main pipeline --runner=all
python -m api
```

Optional overlap guard: `python -m main pipeline --runner=s2_download --lock-file=/path/to/lock`.

## Docker Compose

Run from **`crawler/`**.

| Command | Effect |
|--------|--------|
| `docker compose up -d` | **tor**, **api**, all pipeline services **`s1_fetch` … `s8_upload`** |
| `docker compose --profile pgsql up -d postgres` | Postgres 18 only (profile **`pgsql`**) |
| `docker compose --profile pgsql up -d` | Above **plus** full stack |

Only **`s2_download`** uses Tor (`YT_DLP_PROXY`); other stages clear it in Compose so `.env` does not force a proxy on them.

`DB_URL` for services talking to Compose Postgres: host **`postgres`**, e.g. `postgresql+psycopg2://USER:PASS@postgres:5432/DB`. Ensure **`./works`** exists (locks under `./works/locks`).

## Cron

Pipeline stages match `scheduler.py` (`RUNNERS` / `STAGES`). Each Compose service name equals the `--runner` value (`s1_fetch`, `s2_download`, …). Replace `/path/to/crawler` with this project’s `crawler/` directory; change the schedule as needed.

Example (daily 08:00 `start` for every stage):

```cron
0 8 * * * cd /path/to/crawler && docker compose start s1_fetch
0 8 * * * cd /path/to/crawler && docker compose start s2_download
0 8 * * * cd /path/to/crawler && docker compose start s3_convert
0 8 * * * cd /path/to/crawler && docker compose start s4_subtitle
0 8 * * * cd /path/to/crawler && docker compose start s5_translate_vtt
0 8 * * * cd /path/to/crawler && docker compose start s6_translate_meta
0 8 * * * cd /path/to/crawler && docker compose start s7_hls
0 8 * * * cd /path/to/crawler && docker compose start s8_upload
```

`--runner=all` is not a separate Compose service; run it on the host with `python -m main pipeline --runner=all` (or `python -m scheduler --runner=all`) if you need one process running every stage.
