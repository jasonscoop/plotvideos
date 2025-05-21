from os import getenv
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


ROOT_DIR = Path(__file__).parent.parent.parent
DOWNLOADS_DIR = ROOT_DIR.joinpath("downloads")
DOWNLOADS_DIR.mkdir(exist_ok=True)

POSTGRES_URL=getenv("POSTGRES_URL")

RAPIDAPI_URL=getenv("RAPIDAPI_URL", "https://quality-porn.p.rapidapi.com/search")
RAPIDAPI_KEY=getenv("RAPIDAPI_KEY")

KEYWORDS=getenv("KEYWORDS", "Japan,Phone").split(",")

REDIS_HOST=getenv("REDIS_HOST", "localhost")
REDIS_PORT=getenv("REDIS_PORT", "6379")