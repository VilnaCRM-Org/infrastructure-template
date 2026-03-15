#!/usr/bin/env bash
set -euo pipefail

mkdir -p "${HOME}/.aws"
chmod 700 "${HOME}/.aws"

if [[ ! -f .env ]]; then
  if [[ ! -f .env.empty ]]; then
    echo "error: .env.empty not found; cannot bootstrap .env" >&2
    exit 1
  fi
  install -m 600 .env.empty .env
else
  chmod 600 .env
fi

mkdir -p .pulumi-backend
chmod 700 .pulumi-backend
