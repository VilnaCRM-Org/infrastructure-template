#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="${ROOT_DIR:-$(pwd)}"
QUALITY_ARTIFACT_DIR="${QUALITY_ARTIFACT_DIR:-.artifacts/quality}"
WILY_TARGETS="${WILY_TARGETS:-pulumi policy scripts}"
WILY_CACHE_DIR="${QUALITY_ARTIFACT_DIR}/wily-cache"
WILY_REPORT="${QUALITY_ARTIFACT_DIR}/wily-rank.txt"

read -r -a wily_targets <<<"${WILY_TARGETS}"

mkdir -p "${QUALITY_ARTIFACT_DIR}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1 || ! git rev-parse --verify HEAD >/dev/null 2>&1; then
  cat >"${WILY_REPORT}" <<'EOF'
Wily maintainability report skipped: this workspace does not expose a resolvable git HEAD.
Run the report from a normal repository checkout to build maintainability trends.
EOF
  exit 0
fi

rm -rf "${WILY_CACHE_DIR}"
uv run wily --path "${ROOT_DIR}" --cache "${WILY_CACHE_DIR}" build -n 50 "${wily_targets[@]}" >/dev/null
uv run wily --path "${ROOT_DIR}" --cache "${WILY_CACHE_DIR}" rank . maintainability.mi --limit 20 >"${WILY_REPORT}"
