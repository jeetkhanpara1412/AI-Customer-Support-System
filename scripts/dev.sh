#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d backend/.venv ]; then
  python -m venv backend/.venv
fi

backend/.venv/bin/python -m pip install -q -r backend/requirements.txt -r backend/requirements-dev.txt
if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
fi

cd backend
if [ -f dev.db ] && [ "$(../backend/.venv/bin/python - <<'PY'
import sqlite3
conn = sqlite3.connect("dev.db")
table = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='alembic_version'").fetchone()
print("0" if not table or conn.execute("SELECT COUNT(*) FROM alembic_version").fetchone()[0] == 0 else "1")
PY
)" = "0" ]; then
  rm dev.db
fi
../backend/.venv/bin/alembic upgrade head
if [ ! -f app/ml/artifacts/support_classifier.joblib ]; then
  ../backend/.venv/bin/python -m app.ml.train
fi
FIRST_ADMIN_EMAIL=admin@example.com FIRST_ADMIN_PASSWORD='change-me-for-local-use' \
  ../backend/.venv/bin/python scripts/seed.py

backend_pid=""
frontend_pid=""
cleanup() {
  if [ -n "$frontend_pid" ] && kill -0 "$frontend_pid" 2>/dev/null; then
    kill "$frontend_pid"
  fi
  if [ -n "$backend_pid" ] && kill -0 "$backend_pid" 2>/dev/null; then
    kill "$backend_pid"
  fi
}
trap cleanup EXIT INT TERM

../backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 &
backend_pid=$!

cd "$ROOT_DIR/frontend"
npm ci
npm run dev -- --host 0.0.0.0 &
frontend_pid=$!

wait "$backend_pid" "$frontend_pid"
