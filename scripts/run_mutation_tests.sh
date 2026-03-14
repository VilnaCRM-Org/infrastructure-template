#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"

UV_BIN="${UV_BIN:-uv}"
if ! command -v "${UV_BIN}" >/dev/null 2>&1; then
  if [ -x "/usr/local/bin/uv" ]; then
    UV_BIN="/usr/local/bin/uv"
  fi
fi

if ! command -v "${UV_BIN}" >/dev/null 2>&1; then
  echo "uv executable not found. Set UV_BIN or install uv." >&2
  exit 127
fi

"${UV_BIN}" run mutmut run \
  --paths-to-mutate pulumi/app \
  --runner "${UV_BIN} run pytest -q tests/unit tests/integration"
