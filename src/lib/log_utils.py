from datetime import datetime, timedelta, timezone
import logging

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