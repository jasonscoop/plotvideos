from os import getenv
from pathlib import Path

from dotenv import load_dotenv

from crawler.utils.env_utils import get_str, get_int, get_bool, get_float

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent.parent
WORKS_DIR = ROOT_DIR / "works"

VIDEOS_DIR = WORKS_DIR.joinpath("videos")
VIDEOS_DIR.mkdir(exist_ok=True)
LOGS_DIR = WORKS_DIR.joinpath("logs")
LOGS_DIR.mkdir(exist_ok=True)
MODELS_DIR = WORKS_DIR.joinpath("models")

DB_URL = getenv("DB_URL")

RAPIDAPI_URL = getenv("RAPIDAPI_URL", "https://quality-porn.p.rapidapi.com/search")
RAPIDAPI_KEY = getenv("RAPIDAPI_KEY")
RAPIDAPI_FETCH_PAGE = get_int("RAPIDAPI_FETCH_PAGE", 2)

RAPIDAPI_AI_TRANSLATE_KEY_URL = getenv("RAPIDAPI_AI_TRANSLATE_KEY_URL", "")
RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL = getenv(
    "RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL", ""
)

YT_DLP_PROXY = getenv("YT_DLP_PROXY", None)

MAX_ACCEPT_VIDEO_SIZE = get_int("MAX_ACCEPT_VIDEO_SIZE", 1 * 1024 * 1024 * 1024)  # 1GB maximum
MIN_ACCEPT_DURATION = get_int("MIN_ACCEPT_DURATION", 3 * 60)  # 3 mins
SUBTITLE_TOKEN_RATIO_THRESHOLD = get_float("SUBTITLE_TOKEN_RATIO_THRESHOLD", 0.2)

LLM_BASE_URL = getenv("LLM_BASE_URL")
LLM_MODEL = getenv("LLM_MODEL")
LLM_API_KEY = getenv("LLM_API_KEY")
LLM_API_VERSION = getenv("LLM_API_VERSION")

B2_APPLICATION_KEY_ID = getenv("B2_APPLICATION_KEY_ID")
B2_APPLICATION_KEY = getenv("B2_APPLICATION_KEY")
B2_BUCKET_NAME = getenv("B2_BUCKET_NAME")
B2_CDN_DOMAIN = getenv("B2_CDN_DOMAIN", "https://play.luckvideos.com")

WHISPER_MODEL = getenv("WHISPER_MODEL", "large-v3-turbo")
WHISPER_DEVICE = getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_CPU_THREADS = get_int("WHISPER_CPU_THREADS", 1)
WHISPER_NUM_WORKERS = get_int("WHISPER_NUM_WORKERS", 2)
WHISPER_LOCAL_FILES_ONLY = get_bool("WHISPER_LOCAL_FILES_ONLY", False)
WHISPER_BEAM_SIZE = get_int("WHISPER_BEAM_SIZE", 1)
WHISPER_DEVICE_INDEX = get_int("WHISPER_DEVICE_INDEX", 0)

NLLB_MODEL = getenv("NLLB_MODEL", "facebook/nllb-200-distilled-600M")
NLLB_DEVICE = getenv("NLLB_DEVICE", "cpu")
NLLB_MAX_LENGTH = get_int("NLLB_MAX_LENGTH", 512)

S1_FETCH_MAX_PAGES: int = get_int("S1_FETCH_MAX_PAGES", 10)
S2_DOWNLOAD_BATCH_SIZE: int = get_int("S2_DOWNLOAD_BATCH_SIZE", 5)
S3_CONVERT_BATCH_SIZE: int = get_int("S3_CONVERT_BATCH_SIZE", 5)
S4_SUBTITLE_BATCH_SIZE: int = get_int("S4_SUBTITLE_BATCH_SIZE", 1)
S5_TRANSLATE_VTT_BATCH_SIZE: int = get_int("S5_TRANSLATE_VTT_BATCH_SIZE", 5)
S6_TRANSLATE_META_BATCH_SIZE: int = get_int("S6_TRANSLATE_META_BATCH_SIZE", 5)
S7_UPLOAD_BATCH_SIZE: int = get_int("S7_UPLOAD_BATCH_SIZE", 5)

