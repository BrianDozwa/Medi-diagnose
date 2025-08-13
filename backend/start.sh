#!/usr/bin/env bash
set -euo pipefail

# Local usage:
# 1) Create a venv (recommended):
#    python3 -m venv .venv && source .venv/bin/activate
# 2) Install deps:
#    pip install -r backend/requirements.txt
# 3) (Optional) Configure env vars:
#    cp backend/.env.example backend/.env && edit values as needed
#    export $(grep -v '^#' backend/.env | xargs) || true
# 4) Run the API (from the backend/ directory):
#    ./start.sh

# Start FastAPI with auto-reload. API_PORT can be set via env.
uvicorn app.main:app --host 0.0.0.0 --port "${API_PORT:-8000}" --reload 