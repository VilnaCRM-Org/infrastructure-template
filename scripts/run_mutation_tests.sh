#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "${ROOT_DIR}"

poetry run mutmut run \
  --paths-to-mutate pulumi/pulumi_app \
  --runner "poetry run pytest -q tests/unit tests/integration"
