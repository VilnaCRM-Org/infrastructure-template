#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
POLICY_DIR="${ROOT_DIR}/policy"
POLICY_VENV="${POLICY_VENV:-/home/dev/.venvs/infrastructure-template}"
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

if ! "${POLICY_PYTHON}" - <<'PY' >/dev/null 2>&1
import pulumi
import pulumi_policy
PY
then
    (
        cd "${ROOT_DIR}"
        UV_PROJECT_ENVIRONMENT="${POLICY_VENV}" uv sync --frozen --all-groups >/dev/null
    )
fi

if ! "${POLICY_PYTHON}" - <<'PY' >/dev/null 2>&1
import pulumi
import pulumi_policy
PY
then
    echo "error: shared policy interpreter is missing pulumi or pulumi-policy" >&2
    echo "hint: rebuild the development image to refresh the uv-managed dependencies" >&2
    exit 1
fi
