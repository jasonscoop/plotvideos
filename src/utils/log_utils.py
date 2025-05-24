import time
from datetime import datetime, timedelta, timezone
import logging
from functools import wraps

from src.lib.config import LOGS_DIR


def get_now():
    return datetime.now(timezone.utc)

def get_today():
    return get_now().strftime("%Y-%m-%d")


def init_logging(category: str):
    filename = LOGS_DIR.joinpath(category).joinpath(get_today() + ".log")
    filename.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(format='[%(asctime)s] [%(levelname)s] %(message)s',
                        datefmt='%Y-%d-%m %I:%M:%S',
                        level=logging.INFO,
                        handlers=[logging.FileHandler(filename), logging.StreamHandler()])


def log_time(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logging.info(f"Function '{func.__name__}' took {duration:.1f} seconds")
        return result
    return wrapper