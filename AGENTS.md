# AGENTS

This repository is a Pulumi infrastructure template for AWS. Agents should keep the scope tight, prefer testable changes, and avoid turning local validation into real cloud mutations unless the user explicitly asks for that.

## Working rules
1. Make the smallest change that satisfies the task.
2. Prefer updating tests, docs, or examples before broad workflow refactors.
3. Run the narrowest useful validation for the files you touched.
4. Use `pulumi -C pulumi ...` for direct Pulumi CLI commands.
5. Keep CI credential-free by default. Structural, unit, integration-smoke, mutation, and CLI checks should not require live AWS access.

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
1. Default validation should use Pulumi mocks, dry runs, or local-only smoke tests.
2. Preview before apply when working against a real stack.
3. Prefer ephemeral validation stacks such as `pr-<number>` or `smoke` for manual checks.
4. Destroy ephemeral validation stacks after the check completes.

## Review-driven changes
1. Use `gh pr view <PR>` and `gh pr checks <PR>` for context.
2. Pull review threads with `gh api graphql` and resolve every actionable thread.
3. Keep refactors minimal and directly tied to review feedback.
4. Update `docs/` whenever local workflows, CI expectations, or credential requirements change.
5. Re-run the relevant checks before pushing.
