import argparse
import asyncio
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

from loguru import logger

from core.config import SKIP_STAGES, validate_config
from service import (
    s1_fetch, s2_download, s3_convert, s4_subtitle,
    s5_translate_vtt, s6_translate_meta, s7_hls, s8_upload,
)
from utils.log_utils import init_logging
from utils.telegram_notify import notify_stage_failure

BatchFn = Callable[[Optional[int]], Tuple[bool, Optional[int]]]


@dataclass
class StageConfig:
    name: str
    process_batch: BatchFn


STAGES: list[StageConfig] = [
    StageConfig("s1_fetch", s1_fetch.process_batch),
    StageConfig("s2_download", s2_download.process_batch),
    StageConfig("s3_convert", s3_convert.process_batch),
    StageConfig("s4_subtitle", s4_subtitle.process_batch),
    StageConfig("s5_translate_vtt", s5_translate_vtt.process_batch),
    StageConfig("s6_translate_meta", s6_translate_meta.process_batch),
    StageConfig("s7_hls", s7_hls.process_batch),
    StageConfig("s8_upload", s8_upload.process_batch),
]

_skip_set = set(SKIP_STAGES)
_known = {s.name for s in STAGES}
for _name in SKIP_STAGES:
    if _name not in _known:
        logger.warning(f"SKIP_STAGES contains unknown stage: {_name}")
ACTIVE_STAGES = [s for s in STAGES if s.name not in _skip_set]


async def _run_stage(stage: StageConfig) -> None:
    last_id: Optional[int] = None
    logger.info(f"[{stage.name}] stage started")

    while True:
        try:
            had_work, last_id = await asyncio.to_thread(stage.process_batch, last_id)
        except Exception as e:
            logger.exception(f"[{stage.name}] batch failed")
            notify_stage_failure(stage.name, e)
            break

        if not had_work:
            logger.info(f"[{stage.name}] queue empty, exiting")
            break

    logger.info(f"[{stage.name}] stage stopped")


async def run_all() -> None:
    if not ACTIVE_STAGES:
        logger.error("No stages to run after SKIP_STAGES; check SKIP_STAGES")
        return

    skipped = _skip_set & _known
    if skipped:
        logger.info(f"Scheduler starting without stages: {sorted(skipped)}")
    else:
        logger.info("Scheduler starting — all stages running concurrently")
    try:
        await asyncio.gather(*[_run_stage(stage) for stage in ACTIVE_STAGES])
    except asyncio.CancelledError:
        logger.info("Scheduler cancelled (Ctrl+C)")
    logger.info("Scheduler stopped")


RUNNERS = {
    "s1_fetch":          s1_fetch.fetch_and_save_videos,
    "s2_download":       s2_download.download_videos,
    "s3_convert":        s3_convert.convert_videos,
    "s4_subtitle":       s4_subtitle.subtitle_videos,
    "s5_translate_vtt":  s5_translate_vtt.process_subtitled_videos,
    "s6_translate_meta": s6_translate_meta.translate_meta_infos,
    "s7_hls":            s7_hls.generate_hls_videos,
    "s8_upload":         s8_upload.upload_videos,
}


def run_runner(runner: str, *, init_log: bool = True) -> None:
    if init_log:
        init_logging(runner)
    validate_config()
    logger.info(f"Starting runner: {runner}")
    if runner == "all":
        asyncio.run(run_all())
    elif runner in RUNNERS:
        RUNNERS[runner]()
    else:
        raise ValueError(
            f"Invalid runner: {runner}. "
            f"Choose from: all, {', '.join(RUNNERS)}"
        )


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
    try:
        run_runner(args.runner)
    except ValueError as e:
        logger.error(str(e))
        exit(1)
