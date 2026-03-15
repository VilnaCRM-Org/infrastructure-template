#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_MUTATION_TEST_TARGETS="tests/unit/test_environment_component.py tests/unit/test_guardrails.py"

cd "${ROOT_DIR}"

UV_BIN="${UV_BIN:-uv}"
if ! command -v "${UV_BIN}" >/dev/null 2>&1 && [ -x "/usr/local/bin/uv" ]; then
  UV_BIN="/usr/local/bin/uv"
fi

if ! command -v "${UV_BIN}" >/dev/null 2>&1; then
  echo "uv executable not found. Set UV_BIN or install uv." >&2
  exit 127
fi

MUTATION_PATHS="${MUTATION_PATHS:-pulumi/app}"
MUTATION_TEST_TARGETS="${MUTATION_TEST_TARGETS:-${DEFAULT_MUTATION_TEST_TARGETS}}"
MUTATION_TESTS_DIR="${MUTATION_TESTS_DIR:-tests/unit}"
MUTATION_RUNNER="${MUTATION_RUNNER:-${UV_BIN} run pytest -q ${MUTATION_TEST_TARGETS}}"
MUTATION_COVERAGE_TARGETS="${MUTATION_COVERAGE_TARGETS:-${MUTATION_TEST_TARGETS}}"

read -r -a mutation_coverage_targets <<<"${MUTATION_COVERAGE_TARGETS}"

rm -f .coverage .coverage.*
"${UV_BIN}" run pytest -q --cov=pulumi/app --cov-branch --cov-report= "${mutation_coverage_targets[@]}"

"${UV_BIN}" run mutmut run \
  --paths-to-mutate "${MUTATION_PATHS}" \
  --runner "${MUTATION_RUNNER}" \
  --tests-dir "${MUTATION_TESTS_DIR}" \
  --use-coverage
