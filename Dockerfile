FROM python:3.12-slim

RUN apt-get update  \
    && apt-get install -y --no-install-recommends \
    build-essential \
    mailcap \
    libmagic1 \
    ffmpeg \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /workspace
ENV PYTHONPATH=.

COPY pyproject.toml .
COPY uv.lock .

RUN uv pip install --system -r pyproject.toml
RUN uv pip install --system --upgrade yt-dlp
COPY crawler/ crawler/
COPY web/ web/
COPY scripts/ scripts/


