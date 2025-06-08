#!/bin/bash

if [ -z "$1" ]; then
  echo "Usage: $0 <service_name1>"
  exit 1
fi

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
services=("$@")

(cd "$script_dir" && \
git pull origin main && \
docker compose -f docker-compose.yml up -d --build --no-deps "${services[@]}")

