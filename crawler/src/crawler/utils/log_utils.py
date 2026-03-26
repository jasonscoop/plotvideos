import time
from datetime import datetime, timedelta, timezone
from loguru import logger
from functools import wraps

from crawler.core.config import LOGS_DIR


def get_now():
    return datetime.now(timezone.utc)


def get_today():
    return get_now().strftime("%Y-%m-%d")


def init_logging(category: str):
    filename = LOGS_DIR.joinpath(category).joinpath(get_today() + ".log")
    filename.parent.mkdir(parents=True, exist_ok=True)
    logger.add(filename, rotation="10 MB", retention="7 days", compression="zip")


def log_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"Function '{func.__name__}' took {duration:.1f} seconds")
        return result

    return wrapper
