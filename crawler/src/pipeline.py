import argparse
import sys
from pathlib import Path

from loguru import logger

from scheduler import RUNNERS, run_runner
from utils.log_utils import init_logging
from utils.process_lock import exclusive_lock


def _cmd_pipeline(args: argparse.Namespace) -> int:
    init_logging(args.runner)
    if args.lock_file is not None:
        with exclusive_lock(Path(args.lock_file)) as acquired:
            if not acquired:
                logger.warning(
                    "Lock held by another process; skipping run "
                    f"(exit {args.exit_code_if_locked})"
                )
                return args.exit_code_if_locked
            return _run_pipeline(args.runner)
    return _run_pipeline(args.runner)


def _run_pipeline(runner: str) -> int:
    try:
        run_runner(runner, init_log=False)
    except ValueError as e:
        logger.error(str(e))
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(prog="pipeline")
    parser.add_argument(
        "--runner",
        required=True,
        help=(
            "Stage: 'all' for all stages concurrently, "
            f"or one of: {', '.join(RUNNERS)}"
        ),
    )
    parser.add_argument(
        "--lock-file",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Exclusive lock path; if another run holds it, exit without running "
            "(for cron / overlapping schedules)"
        ),
    )
    parser.add_argument(
        "--exit-code-if-locked",
        type=int,
        choices=(0, 1),
        default=0,
        help="Exit code when lock is not acquired (default: 0 for cron-friendly skip)",
    )
    args = parser.parse_args()
    return _cmd_pipeline(args)


if __name__ == "__main__":
    sys.exit(main())
