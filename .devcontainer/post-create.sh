#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -f backend/.env ]; then
  cp backend/.env.example backend/.env
fi

set_env_value() {
  local key="$1"
  local value="$2"
  if grep -q "^${key}=" backend/.env; then
    sed -i "s#^${key}=.*#${key}=${value}#" backend/.env
  else
    printf '%s=%s\n' "$key" "$value" >> backend/.env
  fi
}

set_env_value ENV development
set_env_value DATABASE_URL sqlite:///./dev.db
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

python -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt -r backend/requirements-dev.txt
npm ci --prefix frontend
if [ ! -f frontend/.env ]; then
  cp frontend/.env.example frontend/.env
fi
for key in VITE_APP_ENV VITE_DEMO_ADMIN_EMAIL VITE_DEMO_ADMIN_PASSWORD VITE_DEMO_USER_EMAIL VITE_DEMO_USER_PASSWORD; do
  if ! grep -q "^${key}=" frontend/.env; then
    grep "^${key}=" frontend/.env.example >> frontend/.env
  fi
done

(
  cd backend
  .venv/bin/alembic upgrade head
  if [ ! -f app/ml/artifacts/support_classifier.joblib ]; then
    .venv/bin/python -m app.ml.train
  fi
  .venv/bin/python scripts/seed.py
)
