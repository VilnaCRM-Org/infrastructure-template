#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PYTHONPATH="${ROOT_DIR}/pulumi:${PYTHONPATH:-}"

cd "${ROOT_DIR}"

mutmut run \
  --paths-to-mutate pulumi/pulumi_app \
  --runner "pytest -q tests/unit tests/integration"
