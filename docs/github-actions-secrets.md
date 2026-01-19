# GitHub Actions Secrets

The CI test workflows use a local Pulumi backend and do not require cloud credentials by default. Configure secrets only when you enable deployments, release automation, or template synchronization.

## Pulumi and AWS Secrets (for deploys)

| Secret | Purpose | Notes |
| --- | --- | --- |
| `AWS_ACCESS_KEY_ID` | Authenticate AWS API calls | Optional if you use GitHub OIDC; pair with `AWS_SECRET_ACCESS_KEY`. |
| `AWS_SECRET_ACCESS_KEY` | Authenticate AWS API calls | Store the matching secret key when using static IAM users. |
| `PULUMI_ACCESS_TOKEN` | Authenticate against the Pulumi Service | Required when using the Pulumi Service backend. Generate in the Pulumi UI under **Settings → Access Tokens**. |

### Using GitHub OIDC Instead of Static Keys

If you prefer short-lived credentials:

1. Create an IAM role that trusts your GitHub organization/repository via OpenID Connect.
2. Grant the role permissions to manage the stack resources.
3. Store the role ARN as `AWS_OIDC_ROLE_ARN` (or another name) and update the workflow to assume it.

See [Configuring OpenID Connect in cloud providers](https://docs.github.com/en/actions/security-guides/security-hardening-your-deployments/configuring-openid-connect-in-cloud-providers) for detailed steps.

## Release Automation Secrets

| Secret | Purpose | Notes |
| --- | --- | --- |
| `REPO_GITHUB_TOKEN` | Publish changelog-based releases | Optional; if unset, workflows fall back to `GITHUB_TOKEN` with `contents:write`. |

## Template Sync Secrets

Choose one authentication strategy for the template sync workflows:

| Secret | Purpose | Notes |
| --- | --- | --- |
| `PERSONAL_ACCESS_TOKEN` | Authenticate template sync (PAT workflow) | Required by `.github/workflows/template-sync-pat.yml`. Needs repo write access. |
| `VILNACRM_APP_ID` | GitHub App ID for template sync | Required by `.github/workflows/template-sync-app.yml`. |
| `VILNACRM_APP_PRIVATE_KEY` | GitHub App private key for template sync | Required by `.github/workflows/template-sync-app.yml`. Store the PEM contents. |

## Setting Secrets

1. Navigate to **Settings → Secrets and variables → Actions** in your GitHub repository.
2. Click **New repository secret** for each value listed above.
3. If several repositories share the same infrastructure credentials, consider using organization secrets instead.

Rotate credentials regularly and audit workflow runs for unexpected usage.
