#!/usr/bin/env bash
set -euo pipefail

if [[ "${PULUMI_REQUIRE_SHARED_BACKEND:-false}" == "true" ]]; then
  if [[ -z "${PULUMI_BACKEND_URL:-}" ]]; then
    echo "error: PULUMI_BACKEND_URL must be set for privileged previews." >&2
    exit 1
  fi
else
  export PULUMI_BACKEND_URL="${PULUMI_BACKEND_URL:-file:///workspace/.pulumi-backend}"
fi

make test-preview

if [[ -n "${GITHUB_STEP_SUMMARY:-}" ]]; then
  if [[ -f .artifacts/pulumi-preview/summary.md ]]; then
    cat .artifacts/pulumi-preview/summary.md >>"${GITHUB_STEP_SUMMARY}"
  else
    printf "Pulumi preview completed without a rendered summary artifact.\n" >>"${GITHUB_STEP_SUMMARY}"
  fi
fi
