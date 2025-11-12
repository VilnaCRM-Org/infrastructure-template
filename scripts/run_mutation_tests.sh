#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PYTHONPATH="${ROOT_DIR}/pulumi:${PYTHONPATH:-}"

# Ensure Pulumi CLI is available for integration tests
if ! command -v pulumi >/dev/null 2>&1; then
  curl -fsSL https://get.pulumi.com | sh >/tmp/pulumi-install.log
  export PATH="$HOME/.pulumi/bin:${PATH}"
fi

cd "${ROOT_DIR}"

mutmut run \
  --paths-to-mutate pulumi/pulumi_app \
  --runner "pytest -q tests/unit tests/integration"
