from os import getenv
from dotenv import load_dotenv

load_dotenv()

POSTGRES_URL=getenv("POSTGRES_URL")

RAPIDAPI_URL=getenv("RAPIDAPI_URL", "https://quality-porn.p.rapidapi.com/search")
RAPIDAPI_KEY=getenv("RAPIDAPI_KEY")

KEYWORDS=getenv("KEYWORDS", "Japan,Phone").split(",")

REDIS_HOST=getenv("REDIS_HOST", "localhost")
REDIS_PORT=getenv("REDIS_PORT", "6379")