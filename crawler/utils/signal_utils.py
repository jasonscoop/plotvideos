import signal

from loguru import logger

_stop = False


def setup_graceful_shutdown():
    def handler(signum, frame):
        global _stop
        _stop = True
        logger.info(f"Signal {signum} received, stopping after current batch")

    try:
        signal.signal(signal.SIGTERM, handler)
        signal.signal(signal.SIGINT, handler)
    except (ValueError, OSError):
        pass  # Not the main thread; skip signal registration


def should_stop() -> bool:
    return _stop
