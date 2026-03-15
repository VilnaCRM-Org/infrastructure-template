#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
PULUMI_DIR="${PULUMI_DIR:-${ROOT_DIR}/pulumi}"
POLICY_PACK_DIR="${POLICY_PACK_DIR:-${ROOT_DIR}/policy}"
PREVIEW_ARTIFACT_DIR="${PREVIEW_ARTIFACT_DIR:-${ROOT_DIR}/.artifacts/pulumi-preview}"
SUMMARY_FILE="${PREVIEW_ARTIFACT_DIR}/summary.md"
BACKEND_URL="${PULUMI_BACKEND_URL:-file://${ROOT_DIR}/.pulumi-backend}"

# Local file-backend previews in this template use an empty passphrase by default.
export PULUMI_CONFIG_PASSPHRASE="${PULUMI_CONFIG_PASSPHRASE-}"

mkdir -p "${PREVIEW_ARTIFACT_DIR}"
rm -f "${PREVIEW_ARTIFACT_DIR}"/*.json "${SUMMARY_FILE}"

"${ROOT_DIR}/scripts/prepare_policy_pack.sh"

mapfile -t STACKS < <(
  if [[ -n "${PULUMI_PREVIEW_STACKS:-}" ]]; then
    tr ', ' '\n' <<<"${PULUMI_PREVIEW_STACKS}" | sed '/^$/d'
  else
    find "${PULUMI_DIR}" -maxdepth 1 -type f -name 'Pulumi.*.yaml' \
      ! -name 'Pulumi.yaml' |
      sed -E 's#.*/Pulumi\.(.+)\.yaml$#\1#' |
      sort
  fi
)

if [[ "${#STACKS[@]}" -eq 0 ]]; then
  echo "error: no Pulumi stack configs found under ${PULUMI_DIR}" >&2
  exit 1
fi

pulumi --cwd "${PULUMI_DIR}" login --non-interactive "${BACKEND_URL}" >/dev/null

for stack in "${STACKS[@]}"; do
  safe_stack="$(printf '%s' "${stack}" | tr -c 'A-Za-z0-9._-' '_')"
  preview_file="${PREVIEW_ARTIFACT_DIR}/${safe_stack}.json"

  pulumi --cwd "${PULUMI_DIR}" stack select "${stack}" --create --non-interactive >/dev/null
  pulumi --cwd "${PULUMI_DIR}" preview \
    --stack "${stack}" \
    --non-interactive \
    --json \
    --policy-pack "${POLICY_PACK_DIR}" \
    >"${preview_file}"

  uv --project "${ROOT_DIR}" run python "${ROOT_DIR}/scripts/pulumi_ci_guardrails.py" summarize "${preview_file}" >>"${SUMMARY_FILE}"
done

cat "${SUMMARY_FILE}"
