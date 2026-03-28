from os import getenv

from dotenv import load_dotenv

from utils.env_utils import get_str, get_int, get_bool, get_float

load_dotenv()

DB_URL = getenv("DB_URL")

RAPIDAPI_URL = getenv("RAPIDAPI_URL", "https://quality-porn.p.rapidapi.com/search")
RAPIDAPI_KEY = getenv("RAPIDAPI_KEY")
RAPIDAPI_FETCH_PAGE = get_int("RAPIDAPI_FETCH_PAGE", 2)

RAPIDAPI_AI_TRANSLATE_KEY_URL = getenv("RAPIDAPI_AI_TRANSLATE_KEY_URL", "")
RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL = getenv(
    "RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL", ""
)
RAPIDAPI_TRANSLATE_MIN_INTERVAL_SEC = get_float(
    "RAPIDAPI_TRANSLATE_MIN_INTERVAL_SEC", 1.0
)
RAPIDAPI_TRANSLATE_FALLBACK_DELAY_SEC = get_float(
    "RAPIDAPI_TRANSLATE_FALLBACK_DELAY_SEC", 2.0
)

YT_DLP_PROXY = getenv("YT_DLP_PROXY", None)

MAX_ACCEPT_VIDEO_SIZE = get_int("MAX_ACCEPT_VIDEO_SIZE", 1 * 1024 * 1024 * 1024)  # 1GB maximum
MIN_ACCEPT_DURATION = get_int("MIN_ACCEPT_DURATION", 3 * 60)  # 3 mins
SUBTITLE_TOKEN_RATIO_THRESHOLD = get_float("SUBTITLE_TOKEN_RATIO_THRESHOLD", 0.15)
MAX_FAILED_NUM = get_int("MAX_FAILED_NUM", 3)

LLM_BASE_URL = getenv("LLM_BASE_URL")
LLM_MODEL = getenv("LLM_MODEL")
LLM_API_KEY = getenv("LLM_API_KEY")
LLM_API_VERSION = getenv("LLM_API_VERSION")

CRAWLER_API_KEY = getenv("CRAWLER_API_KEY", "Test@789")

TELEGRAM_BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN") or None
TELEGRAM_CHAT_ID = getenv("TELEGRAM_CHAT_ID") or None

B2_APPLICATION_KEY_ID = getenv("B2_APPLICATION_KEY_ID")
B2_APPLICATION_KEY = getenv("B2_APPLICATION_KEY")
B2_BUCKET_NAME = getenv("B2_BUCKET_NAME", "luckvideos")
B2_CDN_DOMAIN = getenv("B2_CDN_DOMAIN", "https://play.luckvideos.com")
# Parallel segment uploads for HLS (many small files); tune if you hit B2 rate limits.
B2_UPLOAD_CONCURRENCY: int = get_int("B2_UPLOAD_CONCURRENCY", 16)


def b2_cdn_object_url(object_key: str) -> str:
    """Public CDN URL for a B2 object key."""
    base = B2_CDN_DOMAIN.rstrip("/")
    key = object_key.lstrip("/")
    return f"{base}/{key}"


WHISPER_MODEL = getenv("WHISPER_MODEL", "medium")
WHISPER_DEVICE = getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_CPU_THREADS = get_int("WHISPER_CPU_THREADS", 1)
WHISPER_NUM_WORKERS = get_int("WHISPER_NUM_WORKERS", 2)
WHISPER_LOCAL_FILES_ONLY = get_bool("WHISPER_LOCAL_FILES_ONLY", False)
WHISPER_BEAM_SIZE = get_int("WHISPER_BEAM_SIZE", 1)
WHISPER_DEVICE_INDEX = get_int("WHISPER_DEVICE_INDEX", 0)

S1_FETCH_MAX_PAGES: int = get_int("S1_FETCH_MAX_PAGES", 10)
# Keyword eligibility window and idle backoff when no work: same hours. 0 = no cooldown / poll ~every 60s.
S1_KEYWORD_COOLDOWN_HOURS: int = get_int("S1_KEYWORD_COOLDOWN_HOURS", 24)


def validate_config():
    missing = []
    if not DB_URL:
        missing.append("DB_URL")
    if not RAPIDAPI_KEY:
        missing.append("RAPIDAPI_KEY")
    if RAPIDAPI_AI_TRANSLATE_KEY_URL.strip() and not RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL.strip():
        missing.append("RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL")
    if missing:
        raise EnvironmentError(
            f"Missing required environment variables: {', '.join(missing)}"
        )
S2_DOWNLOAD_BATCH_SIZE: int = get_int("S2_DOWNLOAD_BATCH_SIZE", 5)
S3_CONVERT_BATCH_SIZE: int = get_int("S3_CONVERT_BATCH_SIZE", 5)
S4_SUBTITLE_BATCH_SIZE: int = get_int("S4_SUBTITLE_BATCH_SIZE", 1)
S5_TRANSLATE_VTT_BATCH_SIZE: int = get_int("S5_TRANSLATE_VTT_BATCH_SIZE", 5)
S6_TRANSLATE_META_BATCH_SIZE: int = get_int("S6_TRANSLATE_META_BATCH_SIZE", 5)
S7_UPLOAD_BATCH_SIZE: int = get_int("S7_UPLOAD_BATCH_SIZE", 5)

