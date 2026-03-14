# GitHub Actions Secrets

The structural, unit, integration, mutation, and CLI workflows are local-only and do not require cloud credentials. Secrets are only needed for preview, deploy, release, or template-sync automation.

## Pulumi and AWS secrets

| Secret | Purpose | Notes |
| --- | --- | --- |
| `PULUMI_ACCESS_TOKEN` | Authenticate against the Pulumi Service backend | Optional when using a local backend. Required for preview/deploy to perform real cloud operations; otherwise those jobs skip after the credential preflight. |
| `AWS_ACCESS_KEY_ID` | Static AWS credential for GitHub Actions | Optional when you use GitHub OIDC instead. |
| `AWS_SECRET_ACCESS_KEY` | Secret paired with the access key above | Optional when you use GitHub OIDC instead. |
| `AWS_SESSION_TOKEN` | Session credential for temporary IAM sessions | Optional; only needed when your static credential flow requires it. |
| `AWS_REGION` | Default AWS region for preview/deploy workflows | Optional; defaults to `eu-central-1`. Prefer a repository or organization variable when possible. |
| `AWS_ROLE_TO_ASSUME` | IAM role ARN for GitHub OIDC | Preferred over long-lived static keys. The workflows read it from either `vars.AWS_ROLE_TO_ASSUME` or `secrets.AWS_ROLE_TO_ASSUME`. |

## Preferred setup: GitHub OIDC

The preview and deploy workflows support GitHub OIDC already.

1. Create an IAM role that trusts `token.actions.githubusercontent.com`.
2. Grant the role only the permissions required by the Pulumi stack.
3. Store the role ARN as `AWS_ROLE_TO_ASSUME`.
4. Optionally set `AWS_REGION` as a repository variable or secret.

If `AWS_ROLE_TO_ASSUME` is not set, the workflows fall back to static IAM credentials. If neither OIDC nor static AWS credentials are configured, the preview/deploy jobs exit successfully after the preflight skip instead of failing the template repository.

## Release automation secrets

| Secret | Purpose | Notes |
| --- | --- | --- |
| `VILNACRM_APP_ID` | GitHub App ID used by the release workflow | Required by `.github/workflows/autorelease.yml`. |
| `VILNACRM_APP_PRIVATE_KEY` | GitHub App private key used by the release workflow | Store the PEM contents directly. |

## Template sync secrets

Choose one authentication strategy:

| Secret | Purpose | Notes |
| --- | --- | --- |
| `PERSONAL_ACCESS_TOKEN` | Authenticate template sync through a PAT | Used by `.github/workflows/template-sync-pat.yml`. |
| `VILNACRM_APP_ID` | GitHub App ID for template sync | Used by `.github/workflows/template-sync-app.yml`. |
| `VILNACRM_APP_PRIVATE_KEY` | GitHub App private key for template sync | Used by `.github/workflows/template-sync-app.yml`. |

## Setting secrets

1. Open **Settings -> Secrets and variables -> Actions** in the repository.
2. Add only the secrets required for the workflows you actually use.
3. Prefer repository or organization variables for non-sensitive values such as `AWS_REGION`.
4. Rotate IAM users, GitHub App keys, and PATs regularly.
5. Audit workflow runs for unexpected credential use.
