#!/usr/bin/env bash
# Start the development server with hot-reload enabled.
set -euo pipefail

cd "$(dirname "$0")/.."

exec uv run uvicorn src.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --reload
