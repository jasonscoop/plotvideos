import requests
from urllib.parse import urlparse

from src.config import RAPIDAPI_KEY, RAPIDAPI_URL


def fetch_video_urls(query: str, page: int):
    querystring = {
        "query":query,
        "page":str(page),
        "timeout":"5000"
    }

    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": urlparse(RAPIDAPI_URL).netloc
    }

    response = requests.get(RAPIDAPI_URL, headers=headers, params=querystring)

    print(response.json())


if __name__ == "__main__":
    fetch_video_urls("Chinese", 1)