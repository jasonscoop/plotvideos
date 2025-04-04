from os import getenv
from dotenv import load_dotenv

load_dotenv()


RAPIDAPI_URL=getenv("RAPIDAPI_URL", "https://quality-porn.p.rapidapi.com/search")
RAPIDAPI_KEY=getenv("RAPIDAPI_KEY")

