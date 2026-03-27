import traceback

import requests
from loguru import logger

from core.config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

_TELEGRAM_MAX = 4096


def send_telegram_alert(message: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    text = message if len(message) <= _TELEGRAM_MAX else message[: _TELEGRAM_MAX - 20] + "\n…(truncated)"
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": text,
                "disable_web_page_preview": True,
            },
            timeout=20,
        )
        r.raise_for_status()
    except Exception as e:
        logger.warning(f"Telegram alert failed: {e}")


def notify_stage_failure(stage_name: str, exc: BaseException) -> None:
    tb = "".join(
        traceback.format_exception(type(exc), exc, exc.__traceback__)
    )
    body = f"[TheVideoProject] crawl failed: \n{stage_name}\n\n{type(exc).__name__}: {exc}\n\n{tb}"
    send_telegram_alert(body)
