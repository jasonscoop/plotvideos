FROM python:3.12-slim

RUN apt-get update  \
    && apt-get install -y --no-install-recommends \
    build-essential \
    mime-support \
    libmagic1 \
    ffmpeg \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \

WORKDIR /app
ENV PYTHONPATH="${PYTHONPATH}:."

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY pyproject.toml .
COPY uv.lock .

RUN uv pip install --system -r pyproject.toml
COPY src src

CMD ["python", "s1_fetch.py"]
