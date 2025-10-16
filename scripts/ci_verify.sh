#!/usr/bin/env bash
set -euo pipefail

echo "[ci] Build CodeGraph (no-cache)"
python -m tools.code_graph ./repo --no-cache --dump || { echo "[ci] code_graph failed"; exit 1; }

echo "[ci] Unresolved (non-builtin) calls"
python -m tools.code_graph ./repo --unresolved | sed -n '1,50p' || true

echo "[ci] Static and tests"
mkdir -p logs
make verify || { echo "[ci] verify failed"; exit 1; }

echo "[ci] OK"

