"""
Async scheduler: runs all pipeline stages concurrently in a single process.

Each stage runs as an asyncio task. When a stage finds work it calls its
sync `process_batch` in a thread (via asyncio.to_thread) so the event loop
stays responsive. When a stage's queue is empty it sleeps via an asyncio
Event so a SIGTERM (or Ctrl+C) wakes it up immediately instead of waiting
out the full idle timeout.

Usage:
    python -m crawler.main --runner=all
"""

import asyncio
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from loguru import logger

from crawler.service import (
    s1_fetch,
    s2_download,
    s3_convert,
    s4_subtitle,
    s5_translate_vtt,
    s6_translate_meta,
    s7_upload,
    s8_cleanup,
    s9_publish,
)
from crawler.utils.signal_utils import (
    register_shutdown_event,
    setup_graceful_shutdown,
    should_stop,
)

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
    StageConfig("s7_upload",         s7_upload.process_batch,         300),
    StageConfig("s8_cleanup",        s8_cleanup.process_batch,        3600),
    StageConfig("s9_publish",        s9_publish.process_batch,        300),
]


async def _idle_sleep(seconds: int, shutdown_event: asyncio.Event) -> bool:
    """Sleep for `seconds` or until shutdown is requested.
    Returns True if shutdown was signalled (caller should stop), False if timed out normally."""
    try:
        await asyncio.wait_for(asyncio.shield(shutdown_event.wait()), timeout=seconds)
        return True  # shutdown event fired
    except asyncio.TimeoutError:
        return False  # normal timeout, keep running


async def _run_stage(stage: StageConfig, shutdown_event: asyncio.Event) -> None:
    last_id: Optional[int] = None
    logger.info(f"[{stage.name}] stage started")

    while not should_stop():
        try:
            had_work, last_id = await asyncio.to_thread(stage.process_batch, last_id)
        except Exception as e:
            logger.error(f"[{stage.name}] fatal error — stage stopped: {e}")
            break

        if not had_work:
            logger.debug(f"[{stage.name}] queue empty, sleeping {stage.idle_sleep}s")
            stopped = await _idle_sleep(stage.idle_sleep, shutdown_event)
            if stopped:
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
