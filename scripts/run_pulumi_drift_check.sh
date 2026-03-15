#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PULUMI_DIR="${PULUMI_DIR:-${ROOT_DIR}/pulumi}"
POLICY_PACK_DIR="${POLICY_PACK_DIR:-${ROOT_DIR}/policy}"
BACKEND_URL="${PULUMI_BACKEND_URL:-}"

if [[ ! -d "${PULUMI_DIR}" ]]; then
  echo "error: PULUMI_DIR '${PULUMI_DIR}' does not exist" >&2
  exit 1
fi

# Shared backends may still use passphrase encryption; default to empty only when unset.
export PULUMI_CONFIG_PASSPHRASE="${PULUMI_CONFIG_PASSPHRASE-}"

if [[ -z "${BACKEND_URL}" || "${BACKEND_URL}" == file://* ]]; then
  echo "Skipping drift detection because PULUMI_BACKEND_URL is not configured for a shared backend."
  exit 0
fi

"${ROOT_DIR}/scripts/prepare_policy_pack.sh"

mapfile -t STACKS < <(
  if [[ -n "${PULUMI_DRIFT_STACKS:-}" ]]; then
    tr ', ' '\n' <<<"${PULUMI_DRIFT_STACKS}" | sed '/^$/d'
  else
    find "${PULUMI_DIR}" -maxdepth 1 -type f -name 'Pulumi.*.yaml' \
      ! -name 'Pulumi.yaml' |
      sed -E 's#.*/Pulumi\.(.+)\.yaml$#\1#' |
      sort
  fi
)

if [[ "${#STACKS[@]}" -eq 0 ]]; then
  echo "error: no Pulumi stacks configured for drift detection" >&2
  exit 1
fi

pulumi --cwd "${PULUMI_DIR}" login "${BACKEND_URL}" >/dev/null

for stack in "${STACKS[@]}"; do
  echo "Checking drift for stack ${stack}"
  if ! pulumi --cwd "${PULUMI_DIR}" stack select "${stack}" --non-interactive >/dev/null; then
    echo "error: unable to select existing stack ${stack} for drift detection" >&2
    exit 1
  fi
  pulumi --cwd "${PULUMI_DIR}" preview \
    --stack "${stack}" \
    --non-interactive \
    --refresh \
    --expect-no-changes \
    --policy-pack "${POLICY_PACK_DIR}"
done
