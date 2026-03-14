#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

export COVERAGE_FILE="${COVERAGE_FILE:-${ROOT_DIR}/.coverage}"
export COVERAGE_PROCESS_START="${COVERAGE_PROCESS_START:-${ROOT_DIR}/.coveragerc}"
export COVERAGE_RCFILE="${COVERAGE_RCFILE:-${ROOT_DIR}/.coveragerc}"

exec python -m coverage run -p "$@"
