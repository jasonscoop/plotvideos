"""
Pipeline scheduler and CLI entry point.

Run a single stage:
    python -m scheduler --runner s4_subtitle

Run all stages concurrently:
    python -m scheduler --runner all

The pull API runs separately:
    uvicorn api:app --host 0.0.0.0 --port 8001
"""

import argparse
import asyncio
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from loguru import logger

from core.config import validate_config
from service import (
    s1_fetch, s2_download, s3_convert, s4_subtitle,
    s5_translate_vtt, s6_translate_meta, s7_hls, s8_upload, s9_cleanup,
)
from utils.log_utils import init_logging
from utils.signal_utils import (
    register_shutdown_event, setup_graceful_shutdown, should_stop,
)
from utils.telegram_notify import notify_stage_failure

# ── Async scheduler ───────────────────────────────────────────────────────────

BatchFn = Callable[[Optional[int]], Tuple[bool, Optional[int]]]


@dataclass
class StageConfig:
    name: str
    process_batch: BatchFn
    idle_sleep: int  # seconds to wait when queue is empty


STAGES: list[StageConfig] = [
    StageConfig("s1_fetch",          s1_fetch.process_batch,          3600),
    StageConfig("s2_download",       s2_download.process_batch,       3600),
    StageConfig("s3_convert",        s3_convert.process_batch,        600),
    StageConfig("s4_subtitle",       s4_subtitle.process_batch,       300),
    StageConfig("s5_translate_vtt",  s5_translate_vtt.process_batch,  300),
    StageConfig("s6_translate_meta", s6_translate_meta.process_batch, 300),
    StageConfig("s7_hls",           s7_hls.process_batch,             300),
    StageConfig("s8_upload",        s8_upload.process_batch,          300),
    StageConfig("s9_cleanup",       s9_cleanup.process_batch,        3600),
]


async def _idle_sleep(seconds: int, shutdown_event: asyncio.Event) -> bool:
    """Sleep for `seconds` or until shutdown is signalled.
    Returns True if shutdown fired (caller should stop), False on normal timeout."""
    try:
        await asyncio.wait_for(asyncio.shield(shutdown_event.wait()), timeout=seconds)
        return True
    except asyncio.TimeoutError:
        return False


async def _run_stage(stage: StageConfig, shutdown_event: asyncio.Event) -> None:
    last_id: Optional[int] = None
    logger.info(f"[{stage.name}] stage started")

    while not should_stop():
        try:
            had_work, last_id = await asyncio.to_thread(stage.process_batch, last_id)
        except Exception as e:
            logger.exception(
                f"[{stage.name}] batch failed; retrying after {stage.idle_sleep}s"
            )
            notify_stage_failure(stage.name, e)
            if await _idle_sleep(stage.idle_sleep, shutdown_event):
                break
            continue

        if not had_work:
            logger.debug(f"[{stage.name}] queue empty, sleeping {stage.idle_sleep}s")
            if await _idle_sleep(stage.idle_sleep, shutdown_event):
                break

    logger.info(f"[{stage.name}] stage stopped")


async def run_all() -> None:
    shutdown_event = asyncio.Event()
    register_shutdown_event(shutdown_event)
    setup_graceful_shutdown()

    logger.info("Scheduler starting — all stages running concurrently")
    try:
        await asyncio.gather(*[_run_stage(stage, shutdown_event) for stage in STAGES])
    except asyncio.CancelledError:
        logger.info("Scheduler cancelled (Ctrl+C)")
    logger.info("Scheduler stopped")


# ── Single-stage runners ──────────────────────────────────────────────────────

RUNNERS = {
    "s1_fetch":          s1_fetch.fetch_and_save_videos,
    "s2_download":       s2_download.download_videos,
    "s3_convert":        s3_convert.convert_videos,
    "s4_subtitle":       s4_subtitle.subtitle_videos,
    "s5_translate_vtt":  s5_translate_vtt.process_subtitled_videos,
    "s6_translate_meta": s6_translate_meta.translate_meta_infos,
    "s7_hls":            s7_hls.generate_hls_videos,
    "s8_upload":         s8_upload.upload_videos,
    "s9_cleanup":        s9_cleanup.clean_files,
}


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Video processing pipeline")
    parser.add_argument(
        "--runner",
        required=True,
        help=(
            "Stage to run: 'all' for all stages concurrently, "
            f"or one of: {', '.join(RUNNERS)}"
        ),
    )
    args = parser.parse_args()
    init_logging(args.runner)
    validate_config()
    logger.info(f"Starting runner: {args.runner}")

    if args.runner == "all":
        asyncio.run(run_all())
    elif args.runner in RUNNERS:
        RUNNERS[args.runner]()
    else:
        logger.error(
            f"Invalid runner: {args.runner}. "
            f"Choose from: all, {', '.join(RUNNERS)}"
        )
        exit(1)
