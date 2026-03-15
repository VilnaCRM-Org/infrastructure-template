#!/usr/bin/env bash
set -euo pipefail

COMPOSE_ENV_FILE="${COMPOSE_ENV_FILE:-.env.empty}"
COMPOSE_SERVICE="${COMPOSE_SERVICE:-pulumi}"
PULUMI_DIR="${PULUMI_DIR:-pulumi}"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker: missing" >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "docker compose: missing" >&2
  exit 1
fi

printf "docker: %s\n" "$(docker --version)"
printf "docker compose: %s\n" "$(docker compose version --short)"
printf "effective env file: %s\n" "${COMPOSE_ENV_FILE}"
printf "compose service: %s\n" "${COMPOSE_SERVICE}"
printf "pulumi directory: %s\n" "${PULUMI_DIR}"

if [[ -f "${COMPOSE_ENV_FILE}" ]]; then
  printf "env file present: yes\n"
else
  printf "env file present: no\n" >&2
  exit 1
fi
