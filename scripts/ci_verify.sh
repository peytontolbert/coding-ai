#!/usr/bin/env bash
set -euo pipefail

# CI verification script: static checks, tests, HTML report. Fails build on gates.

ROOT_DIR="$(pwd)"
LOGS_DIR="${ROOT_DIR}/logs"
mkdir -p "${LOGS_DIR}"

echo "[ci] Running static checks..."
python - <<'PY'
import json, os
from verify.static import run_static
ok = run_static()
print(json.dumps({"static_ok": bool(ok)}))
raise SystemExit(0 if ok else 1)
PY

echo "[ci] Running tests..."
if command -v pytest >/dev/null 2>&1; then
  # Allow pytest to determine failure; we do not mask rc
  pytest -q \
    --maxfail=1 \
    --junitxml="${LOGS_DIR}/junit.xml" \
    --cov=. \
    --cov-report=xml:"${LOGS_DIR}/coverage.xml"
else
  echo "pytest not installed, skipping tests" >&2
  exit 1
fi

echo "[ci] Generating HTML report..."
python -m obs.report --logs "${LOGS_DIR}" || true

echo "[ci] Done. Logs at ${LOGS_DIR}"

