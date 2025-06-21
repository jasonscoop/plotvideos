from os import getenv
from pathlib import Path

from dotenv import load_dotenv

from src.utils.env_utils import get_str, get_int

load_dotenv()

ROOT_DIR = Path(__file__).parent.parent.parent
WORKS_DIR = ROOT_DIR / "works"

VIDEOS_DIR = WORKS_DIR.joinpath("videos")
VIDEOS_DIR.mkdir(exist_ok=True)
LOGS_DIR = WORKS_DIR.joinpath("logs")
LOGS_DIR.mkdir(exist_ok=True)
MODELS_DIR = WORKS_DIR.joinpath("models")

POSTGRES_URL = getenv("POSTGRES_URL")

RAPIDAPI_URL = getenv("RAPIDAPI_URL", "https://quality-porn.p.rapidapi.com/search")
RAPIDAPI_KEY = getenv("RAPIDAPI_KEY")
RAPIDAPI_FETCH_PAGE = get_int("RAPIDAPI_FETCH_PAGE", 2)

RAPIDAPI_AI_TRANSLATE_KEY_URL = getenv("RAPIDAPI_AI_TRANSLATE_KEY_URL", "")
RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL = getenv("RAPIDAPI_GOOGLE_TRANSLATE113_KEY_URL", "")

YT_DLP_PROXY = getenv("YT_DLP_PROXY", None)

MAX_ACCEPT_VIDEO_SIZE = int(getenv("MAX_ACCEPT_VIDEO_SIZE", 1 * 1024 * 1024 * 1024))  # 1GB maximum
MIN_ACCEPT_DURATION = int(getenv("MIN_ACCEPT_DURATION", 3 * 60))  # 3 mins
SUBTITLE_TOKEN_RATIO_THRESHOLD = float(getenv("SUBTITLE_TOKEN_RATIO_THRESHOLD", 0.2))

AZURE_SPEECH_KEY = getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION = getenv("AZURE_SPEECH_REGION")

LLM_BASE_URL = getenv("LLM_BASE_URL")
LLM_MODEL = getenv("LLM_MODEL")
LLM_API_KEY = getenv("LLM_API_KEY")
LLM_API_VERSION = getenv("LLM_API_VERSION")

BUNNY_API_KEY = getenv("BUNNY_API_KEY")
BUNNY_LIBRARY_ID = getenv("BUNNY_LIBRARY_ID")
BUNNY_CDN_DOMAIN = getenv("BUNNY_CDN_DOMAIN")

S3_ACCESS_KEY: str = get_str("S3_ACCESS_KEY")
S3_SECRET_KEY: str = get_str("S3_SECRET_KEY")
S3_BUCKET_NAME: str = get_str("S3_BUCKET_NAME")
S3_REGION: str = get_str("S3_REGION", "ap-southeast-1")

FETCH_MAX_PAGES: int = get_int("FETCH_MAX_PAGES", 10)

WHISPER_MODEL = getenv("WHISPER_MODEL", "large-v3-turbo")
WHISPER_DEVICE = getenv("WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = getenv("WHISPER_COMPUTE_TYPE", "int8")
WHISPER_CPU_THREADS = get_int("WHISPER_CPU_THREADS", 1)
WHISPER_NUM_WORKERS = get_int("WHISPER_NUM_WORKERS", 2)
