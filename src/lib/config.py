from os import getenv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


ROOT_DIR = Path(__file__).parent.parent.parent
WORKS_DIR = ROOT_DIR / "works"

VIDEOS_DIR = WORKS_DIR.joinpath("videos")
VIDEOS_DIR.mkdir(exist_ok=True)
LOGS_DIR = WORKS_DIR.joinpath("logs")
LOGS_DIR.mkdir(exist_ok=True)
MODELS_DIR = WORKS_DIR.joinpath("models")

WHISPER_MODELS_DIR = WORKS_DIR.joinpath("models")
WHISPER_MODELS_DIR.mkdir(exist_ok=True)

POSTGRES_URL=getenv("POSTGRES_URL")

RAPIDAPI_URL=getenv("RAPIDAPI_URL", "https://quality-porn.p.rapidapi.com/search")
RAPIDAPI_KEY=getenv("RAPIDAPI_KEY")

KEYWORDS=getenv("KEYWORDS", "Japan,Phone").split(",")

REDIS_HOST=getenv("REDIS_HOST", "localhost")
REDIS_PORT=getenv("REDIS_PORT", "6379")

YT_DLP_PROXY = getenv("YT_DLP_PROXY", None)


AZURE_SPEECH_KEY=getenv("AZURE_SPEECH_KEY")
AZURE_SPEECH_REGION=getenv("AZURE_SPEECH_REGION")

LLM_BASE_URL = getenv("LLM_BASE_URL")
LLM_MODEL=getenv("LLM_MODEL")
LLM_API_KEY=getenv("LLM_API_KEY")
LLM_API_VERSION=getenv("LLM_API_VERSION")