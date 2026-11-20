#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d backend/.venv ]; then
  python -m venv backend/.venv
  backend/.venv/bin/python -m pip install -q -r backend/requirements.txt -r backend/requirements-dev.txt
fi

if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
fi
if [ ! -f frontend/.env ]; then
  cp frontend/.env.example frontend/.env
fi
for key in ADMIN_EMAIL ADMIN_PASSWORD ADMIN_NAME DEMO_USER_EMAIL DEMO_USER_PASSWORD DEMO_USER_NAME; do
  if ! grep -q "^${key}=" backend/.env; then
    if [ "$key" = ADMIN_EMAIL ] && grep -q '^FIRST_ADMIN_EMAIL=' backend/.env; then
      continue
    fi
    if [ "$key" = ADMIN_PASSWORD ] && grep -q '^FIRST_ADMIN_PASSWORD=' backend/.env; then
      continue
    fi
    grep "^${key}=" backend/.env.example >> backend/.env
  fi
done
for key in VITE_APP_ENV VITE_DEMO_ADMIN_EMAIL VITE_DEMO_ADMIN_PASSWORD VITE_DEMO_USER_EMAIL VITE_DEMO_USER_PASSWORD; do
  if ! grep -q "^${key}=" frontend/.env; then
    grep "^${key}=" frontend/.env.example >> frontend/.env
  fi
done
if [ ! -d frontend/node_modules ]; then
  npm ci --prefix frontend
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

BACKEND_LOG="${TMPDIR:-/tmp}/support-system-backend.log"
FRONTEND_LOG="${TMPDIR:-/tmp}/support-system-frontend.log"
BACKEND_PID="${TMPDIR:-/tmp}/support-system-backend.pid"
FRONTEND_PID="${TMPDIR:-/tmp}/support-system-frontend.pid"

if ! curl --silent --fail http://127.0.0.1:8000/api/health >/dev/null; then
  nohup ../backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 \
    >"$BACKEND_LOG" 2>&1 </dev/null &
  echo "$!" >"$BACKEND_PID"
fi

cd "$ROOT_DIR/frontend"
if ! curl --silent --fail http://127.0.0.1:5173/ >/dev/null; then
  nohup npm run dev -- --host 0.0.0.0 --port 5173 \
    >"$FRONTEND_LOG" 2>&1 </dev/null &
  echo "$!" >"$FRONTEND_PID"
fi

for attempt in $(seq 1 60); do
  if curl --silent --fail http://127.0.0.1:8000/api/health >/dev/null &&
    curl --silent --fail http://127.0.0.1:5173/ >/dev/null; then
    printf 'Backend health: '
    curl --silent --show-error http://127.0.0.1:8000/api/health
    printf '\nFrontend: http://localhost:5173/\n'
    printf 'Backend log: %s\nFrontend log: %s\n' "$BACKEND_LOG" "$FRONTEND_LOG"
    exit 0
  fi
  sleep 2
done

echo "Development services did not become ready in 120 seconds." >&2
if [ -f "$BACKEND_LOG" ]; then
  tail -n 40 "$BACKEND_LOG" >&2
fi
if [ -f "$FRONTEND_LOG" ]; then
  tail -n 40 "$FRONTEND_LOG" >&2
fi
exit 1
