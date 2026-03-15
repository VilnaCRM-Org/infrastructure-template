#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEFAULT_MUTATION_TEST_TARGETS="tests/unit/test_environment_component.py tests/unit/test_guardrails.py"

cd "${ROOT_DIR}"

POETRY_BIN="${POETRY_BIN:-poetry}"
if ! command -v "${POETRY_BIN}" >/dev/null 2>&1; then
  POETRY_HOME="${POETRY_HOME:-/opt/poetry}"
  if [ -x "${POETRY_HOME}/bin/poetry" ]; then
    POETRY_BIN="${POETRY_HOME}/bin/poetry"
  fi
fi

if ! command -v "${POETRY_BIN}" >/dev/null 2>&1; then
  echo "Poetry executable not found. Set POETRY_BIN or install Poetry." >&2
  exit 127
fi

MUTATION_PATHS="${MUTATION_PATHS:-pulumi/app}"
MUTATION_TEST_TARGETS="${MUTATION_TEST_TARGETS:-${DEFAULT_MUTATION_TEST_TARGETS}}"
MUTATION_TESTS_DIR="${MUTATION_TESTS_DIR:-tests/unit}"
MUTATION_RUNNER="${MUTATION_RUNNER:-${POETRY_BIN} run pytest -q ${MUTATION_TEST_TARGETS}}"

mutmut_args=(
  run
  --paths-to-mutate "${MUTATION_PATHS}"
  --runner "${MUTATION_RUNNER}"
  --tests-dir "${MUTATION_TESTS_DIR}"
  --use-coverage
)

"${POETRY_BIN}" run mutmut "${mutmut_args[@]}"
