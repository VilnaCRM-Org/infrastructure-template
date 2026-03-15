#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
POLICY_DIR="${ROOT_DIR}/policy"
POLICY_VENV="${POLICY_VENV:-${HOME}/.venvs/infrastructure-template}"
POLICY_VENV_LINK="${POLICY_DIR}/.venv"
POLICY_PYTHON="${POLICY_VENV}/bin/python"
REQUIREMENTS_FILE="${POLICY_DIR}/requirements.txt"

if [ ! -f "${REQUIREMENTS_FILE}" ]; then
  echo "error: policy requirements file not found at ${REQUIREMENTS_FILE}" >&2
  exit 1
fi

if [ ! -x "${POLICY_PYTHON}" ]; then
  echo "error: policy interpreter not found at ${POLICY_PYTHON}" >&2
  echo "hint: rebuild the development image so the shared uv environment exists" >&2
  exit 1
fi

if [ -e "${POLICY_VENV_LINK}" ] && [ ! -L "${POLICY_VENV_LINK}" ]; then
  echo "error: ${POLICY_VENV_LINK} must be a symlink to the shared uv environment" >&2
  echo "hint: remove the existing path and rerun ./scripts/prepare_policy_pack.sh" >&2
  exit 1
fi

ln -sfn "${POLICY_VENV}" "${POLICY_VENV_LINK}"

if ! ROOT_DIR="${ROOT_DIR}" "${POLICY_PYTHON}" - <<'PY' >/dev/null 2>&1; then
import os
import sys

sys.path.insert(0, os.environ["ROOT_DIR"])
import pulumi
import pulumi_policy
import policy.config
import policy.guardrails
import policy.pack
PY
  (
    cd "${ROOT_DIR}"
    UV_PROJECT_ENVIRONMENT="${POLICY_VENV}" uv sync --frozen --all-groups >/dev/null
  )
fi

if ! ROOT_DIR="${ROOT_DIR}" "${POLICY_PYTHON}" - <<'PY' >/dev/null 2>&1; then
import os
import sys

sys.path.insert(0, os.environ["ROOT_DIR"])
import pulumi
import pulumi_policy
import policy.config
import policy.guardrails
import policy.pack
PY
  echo "error: shared policy interpreter is missing Pulumi or repo-local policy modules" >&2
  echo "hint: rebuild the development image to refresh the uv-managed dependencies" >&2
  exit 1
fi
