# Crawler (Python)

Pipeline: fetch → download → convert → subtitles → translate → HLS → upload. FastAPI (`api`) for the player; storage on B2. Code lives under `src/`; entrypoints are `pipeline` (CLI), `scheduler`, and `api`.

## Configuration

`.env` in this directory. Required: **`DB_URL`**, **`RAPIDAPI_KEY`** (not required if `SKIP_STAGES` includes `s1_fetch`). See `src/core/config.py` for the rest.

## Local

From `crawler/` after `uv sync`:

```bash
export PYTHONPATH=src
python -m pipeline --runner=s2_download
python -m pipeline --runner=all
python -m api
```

Each stage runs batches until its queue is empty, then exits (cron controls when the next run starts).

Optional overlap guard: `python -m pipeline --runner=s2_download --lock-file=/path/to/lock`.

## Docker Compose

Run from **`crawler/`**.

`docker compose build` only builds images; it does **not** create containers. To create and run containers, use **`docker compose up -d`** (or `up -d s3_convert` for one service). **`docker compose start`** only wakes **existing** stopped containers—if you never ran `up`, `ps` stays empty.

| Command | Effect |
|--------|--------|
| `docker compose up -d` | **tor**, **api**, all pipeline services **`s1_fetch` … `s8_upload`** |
| `docker compose up -d s3_convert` | Create/start **one** service (and its **`depends_on`**, e.g. **tor** for **`s2_download`**) |
| `docker compose --profile pgsql up -d postgres` | Postgres 18 only (profile **`pgsql`**) |
| `docker compose --profile pgsql up -d` | Above **plus** full stack |

Only **`s2_download`** uses Tor (`YT_DLP_PROXY`); other stages clear it in Compose so `.env` does not force a proxy on them.

`DB_URL` for services talking to Compose Postgres: host **`postgres`**, e.g. `postgresql+psycopg2://USER:PASS@postgres:5432/DB`. Ensure **`./works`** exists (locks under `./works/locks`).

## Cron

Pipeline stages match `scheduler.py` (`RUNNERS` / `STAGES`). Each Compose service name equals the `--runner` value (`s1_fetch`, `s2_download`, …). Replace `/path/to/crawler` with this project’s `crawler/` directory; change the schedule as needed.

Example (daily 08:00; `up -d` works even when the container does not exist yet):

```cron
0 8 * * * cd /path/to/crawler && docker compose up -d s1_fetch
0 8 * * * cd /path/to/crawler && docker compose up -d s2_download
0 8 * * * cd /path/to/crawler && docker compose up -d s3_convert
0 8 * * * cd /path/to/crawler && docker compose up -d s4_subtitle
0 8 * * * cd /path/to/crawler && docker compose up -d s5_translate_vtt
0 8 * * * cd /path/to/crawler && docker compose up -d s6_translate_meta
0 8 * * * cd /path/to/crawler && docker compose up -d s7_hls
0 8 * * * cd /path/to/crawler && docker compose up -d s8_upload
```

After containers exist, `docker compose start s3_convert` is enough to restart a stopped container.

`--runner=all` is not a separate Compose service; run it on the host with `python -m pipeline --runner=all` (or `python -m scheduler --runner=all`) if you need one process running every stage.
