# CI Guardrails

This repository treats infrastructure pull requests as high-risk changes. The
guardrail layer below is designed to catch the common failure modes of
AI-generated Pulumi and AWS code before anyone merges or applies it.

## Required PR checks

These checks are intended to be marked as required in branch protection:

| Check | Local command | Purpose |
| --- | --- | --- |
| `Preview` | `make test-preview` | Produces a non-destructive Pulumi preview artifact for every configured stack |
| `Destructive Diff Gate` | `make test-destructive-diff` | Blocks deletes and replacements of critical infrastructure unless explicitly approved |
| `IAM Validation` | `make test-iam-validation` | Validates previewed IAM policies with AWS IAM Access Analyzer |
| `Secrets Scan` | `make test-secrets` | Runs Gitleaks against the working tree |
| `Dependency Audit` | `make test-deps-security` | Audits Python dependencies with `pip-audit --strict` |
| `Actionlint` | `make test-actionlint` | Lints GitHub Actions workflow syntax and common security issues |
| `CodeQL (python)` | GitHub-native | Scans Python code for security issues |
| `CodeQL (actions)` | GitHub-native | Scans workflow code for insecure patterns |

`make test-security` aggregates the Gitleaks, dependency, and workflow lint
checks. `make test-guardrails` aggregates preview generation, destructive diff
gating, and IAM validation. `make ci-pr` and `make ci` include both batteries.

## Preview model

The preview workflow uses the same Docker workspace and policy pack that local
developers use:

1. `./scripts/prepare_docker_context.sh`
2. `make test-preview`
3. `make test-destructive-diff`
4. `make test-iam-validation`

Preview artifacts are written under `.artifacts/pulumi-preview/` and uploaded to
GitHub Actions. The preview summary is appended to `GITHUB_STEP_SUMMARY` so
reviewers can inspect the plan without digging through raw logs first.

Stack selection follows this order:

1. `PULUMI_PREVIEW_STACKS` repo variable if set
2. committed `pulumi/Pulumi.<stack>.yaml` files

The current template ships with `Pulumi.dev.yaml`, so the default preview target
is `dev`.

For local runs, the Makefile exports `GITHUB_TOKEN` from `gh auth token` when
the GitHub CLI is already authenticated. This avoids anonymous GitHub API rate
limits during Pulumi provider plugin resolution without introducing a committed
secret or a separate local setup step.

## Destructive change gate

The destructive-diff gate fails when the preview proposes deletes or
replacements against critical resource families such as:

- VPC and networking primitives
- IAM roles and policies
- KMS keys
- S3 buckets
- RDS and other database resources
- Secrets Manager resources
- Route53 records
- EKS resources

Intentional destructive changes must be reviewed manually and then approved with
the pull-request label `allow-destructive-infra-change`. The label is the only
supported override because it leaves an auditable trail in GitHub.

## IAM validation

`scripts/pulumi_ci_guardrails.py validate-iam` extracts IAM policy documents
from the preview artifact and validates them with AWS IAM Access Analyzer.

Current behavior:

- No IAM policies in the preview: the check exits successfully and prints a
  short note
- IAM policies in the preview with valid AWS credentials: findings of type
  `ERROR` and `SECURITY_WARNING` fail the check
- IAM policies in the preview without valid AWS credentials: the check fails so
  maintainers do not accidentally merge unvalidated IAM changes

This complements the custom Pulumi CrossGuard pack. The policy pack blocks
wildcard IAM permissions in repository code; Access Analyzer adds AWS-native
semantic validation for the rendered policy documents.

## OIDC-based AWS access

The guardrail workflows are OIDC-first. They do not use long-lived
`AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` repository secrets.

Required repository variables:

| Variable | Purpose |
| --- | --- |
| `AWS_OIDC_ROLE_ARN` | IAM role assumed by preview, IAM validation, and drift jobs |
| `AWS_REGION` | AWS region used by `configure-aws-credentials` |
| `PULUMI_BACKEND_URL` | Shared Pulumi backend for real preview and drift checks |
| `PULUMI_PREVIEW_STACKS` | Optional comma-separated stack list for preview |
| `PULUMI_DRIFT_STACKS` | Optional comma-separated stack list for nightly drift checks |

Optional repository secrets:

| Secret | Purpose |
| --- | --- |
| `PULUMI_ACCESS_TOKEN` | Required only when the backend is the Pulumi Service |
| `PULUMI_CONFIG_PASSPHRASE` | Required only for passphrase-protected backends |

### Example IAM trust policy

Replace the account ID, organization, and repository name with your own values:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::<ACCOUNT_ID>:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": [
            "repo:VilnaCRM-Org/infrastructure-template:pull_request",
            "repo:VilnaCRM-Org/infrastructure-template:ref:refs/heads/main"
          ]
        }
      }
    }
  ]
}
```

## Nightly-only checks

Nightly workflows are visible but do not block pull requests:

| Check | Purpose |
| --- | --- |
| `Drift Detection` | Runs `pulumi preview --refresh --expect-no-changes` against configured shared stacks |
| `Scorecard` | Runs OpenSSF Scorecard and uploads SARIF results for repository health visibility |

Drift detection intentionally skips when `PULUMI_BACKEND_URL` is not configured
for a shared backend. Running a drift job against an ephemeral file backend on a
fresh GitHub runner would be misleading.

## Manual maintainer follow-up

The workflows are committed in this repository, but maintainers still need to:

1. create the GitHub OIDC IAM role in AWS
2. set the repository variables and optional secrets listed above
3. mark the required PR checks in GitHub branch protection
4. decide whether production repositories want stricter stack lists or narrower
   IAM role scopes than the template defaults

## Current limitations

- CodeQL is GitHub-native; the repository keeps the workflow under structural
  test coverage, but there is no local `make` equivalent
- The custom VilnaCRM CrossGuard pack is the enforced policy-pack layer in this
  template; the workflow does not vendor the Node-based AWSGuard package into
  the Python/uv Docker image
- IAM validation is only as complete as the preview artifact; policies that are
  created entirely outside Pulumi still need separate review
