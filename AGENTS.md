# AGENTS

This repository is a Pulumi-based infrastructure template. Agents should keep changes minimal, preserve the local developer workflow, and avoid introducing hidden cloud dependencies into CI.

## Working rules

1. Make the smallest change that satisfies the task.
2. Prefer updating tests, docs, and examples before widening release or deployment behavior.
3. Run the narrowest useful validation for the files you touched.
4. Use `pulumi -C pulumi ...` for direct Pulumi CLI commands.
5. Use `uv run ...` for Python CLI commands instead of invoking tools directly from the global environment.
6. Seed local `uv` environments with `export UV_PROJECT_ENVIRONMENT="${HOME}/.venvs/infrastructure-template"; uv venv --seed "${UV_PROJECT_ENVIRONMENT}"` before syncing if you need to run Pulumi Automation outside Docker.
7. Keep the structural, policy, quality, unit, integration, mutation, CLI, and aggregate local-battery suites runnable without live AWS credentials.
8. Use `make ci-pr` when you want the non-mutation GitHub PR battery, `make ci` for the full local superset including mutation, and `make test` for the faster non-mutation developer battery.
9. Use `make doctor` before debugging local Docker or Compose issues.
10. Reuse `./scripts/prepare_docker_context.sh` when changing Docker-backed CI jobs so setup remains consistent across workflows.
11. Keep `./scripts/prepare_policy_pack.sh`, `policy/PulumiPolicy.yaml`, `policy/.venv`, and the shared `uv` environment contract aligned when changing Pulumi policy-pack behavior.

## Secret handling

These rules are mandatory for AI coding agents in this repository.

1. Never read, print, summarize, diff, or copy raw secret material.
2. Treat the following as off-limits unless the user explicitly asks for a secret-management task:
   - `.env`, `.env.*`, and shell files that export credentials
   - AWS shared credentials/config files, access keys, session tokens, and STS credentials
   - Pulumi stack files or exports containing `secure:` values or `encryptedkey` metadata
   - GitHub Actions secrets, deploy keys, private keys, certificates, kubeconfigs, and token files
3. Never run commands that reveal secrets in terminal output. This includes `env`, `printenv`, `docker compose config`, `docker inspect`, `pulumi config --show-secrets`, `pulumi stack output --show-secrets`, and cloud-secret fetch commands unless the user explicitly requests that exact action.
4. Prefer metadata-only checks such as `aws sts get-caller-identity`, `pulumi stack ls`, and `pulumi config` without secret-revealing flags.
5. When a secret must be set, write it directly with `pulumi config set --secret ...` or the relevant cloud secret store command without echoing the value back into the terminal transcript.
6. Never commit secret values, decrypted outputs, copied stack exports, or temporary files containing secrets.

## Pulumi workflow

1. Structural, quality, unit, integration, mutation, and CLI checks should stay local-backend-friendly.
2. Preview before apply when working against a real stack.
3. Prefer ephemeral validation stacks such as `pr-<number>` or `smoke` for manual checks.
4. Destroy ephemeral validation stacks after the check completes.

## Review-driven changes

1. Use `gh pr view <PR>` and `gh pr checks <PR>` for context.
2. Pull review threads with `gh api graphql` and resolve every actionable thread.
3. Keep refactors minimal and directly tied to review feedback.
4. Update `docs/` whenever the developer workflow, CI surface, or credential contract changes.
5. Re-run the relevant checks before pushing.
6. Keep the Pulumi policy pack under `policy/` aligned with the runtime guardrails in `pulumi/app/`.
