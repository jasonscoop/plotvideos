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
    parser = argparse.ArgumentParser(prog="main")
    sub = parser.add_subparsers(dest="command", required=True)

    p_pipe = sub.add_parser("pipeline", help="Run the video processing pipeline")
    p_pipe.add_argument(
        "--runner",
        required=True,
        help=(
            "Stage: 'all' for all stages concurrently, "
            f"or one of: {', '.join(RUNNERS)}"
        ),
    )
    p_pipe.add_argument(
        "--lock-file",
        type=Path,
        default=None,
        metavar="PATH",
        help=(
            "Exclusive lock path; if another run holds it, exit without running "
            "(for cron / overlapping schedules)"
        ),
    )
    p_pipe.add_argument(
        "--exit-code-if-locked",
        type=int,
        choices=(0, 1),
        default=0,
        help="Exit code when lock is not acquired (default: 0 for cron-friendly skip)",
    )

    args = parser.parse_args()
    if args.command == "pipeline":
        return _cmd_pipeline(args)
    return 1


if __name__ == "__main__":
    sys.exit(main())
