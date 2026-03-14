#!/usr/bin/env bash
set -euo pipefail

mkdir -p "${HOME}/.aws"
chmod 700 "${HOME}/.aws"

if [[ ! -f .env ]]; then
  cp .env.empty .env
fi

mkdir -p .pulumi-backend
