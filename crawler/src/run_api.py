import uvicorn

from uvicorn_log_config import setup_uvicorn_logging

if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8001, log_config=setup_uvicorn_logging())
