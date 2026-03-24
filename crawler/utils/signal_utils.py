import asyncio
import signal
from typing import Optional

from loguru import logger

_stop = False
_shutdown_event: Optional[asyncio.Event] = None


def _on_sigterm(signum, frame):
    global _stop
    _stop = True
    logger.info("SIGTERM received, stopping after current batch")
    if _shutdown_event is not None:
        try:
            loop = asyncio.get_running_loop()
            loop.call_soon_threadsafe(_shutdown_event.set)
        except RuntimeError:
            pass  # no running loop (single-stage mode)


def setup_graceful_shutdown():
    """Register SIGTERM for graceful shutdown.
    SIGINT (Ctrl+C) is intentionally left to Python/asyncio defaults
    so it raises KeyboardInterrupt and exits immediately."""
    try:
        signal.signal(signal.SIGTERM, _on_sigterm)
    except (ValueError, OSError):
        pass  # not the main thread


def register_shutdown_event(event: asyncio.Event):
    """Give the signal handler an asyncio Event to set on SIGTERM,
    so sleeping stages wake up immediately instead of waiting out their timeout."""
    global _shutdown_event
    _shutdown_event = event


def should_stop() -> bool:
    return _stop
