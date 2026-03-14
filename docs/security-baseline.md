# Security Baseline

This template is designed to give DevOps and SRE teams a safe default starting
point rather than a bare Pulumi skeleton. The controls in this guide describe
what is already enforced in the repository and what should remain true as the
template evolves.

## Threat Model

The main risks for this repository are:

- accidental secret disclosure through local tooling, CI logs, or checked-in files
- supply-chain drift in the Docker workspace and GitHub Actions automation
- over-privileged automation tokens in release or deployment workflows
- non-reproducible infrastructure changes that bypass preview and review

The template does not try to eliminate all operational risk. It does aim to make
the safe path the easy path for normal day-to-day infrastructure work.

## Current Built-In Controls

### Container and Supply Chain

- The Docker base image is pinned by digest, not just by tag.
- Pulumi, AWS CLI, `uv`, and Bats downloads are verified with SHA-256 checksums.
- The runtime image carries only the tooling required for development and CI; it
  does not keep the transient download helpers from the build stage.
- Unused Pulumi language hosts are removed to reduce image size and attack
  surface.
- The container defaults disable noisy update checks and the AWS CLI pager so
  automation behaves predictably.

### GitHub Actions

- Actions are pinned to immutable commit SHAs.
- CI workflows use least-privilege `permissions` blocks.
- PR validation workflows use concurrency groups with
  `cancel-in-progress: true` so stale runs do not compete for runners.
- CI jobs define timeouts so hung runs fail fast instead of silently burning
  minutes.
- `actions/checkout` runs with `persist-credentials: false` to avoid leaving a
  writable Git credential behind in the workspace.

### Secrets and Identity

- Local developer overrides belong in `.env`, which stays git-ignored.
- `.env.empty` is the committed fallback used to keep the Docker and Make flows
  runnable without real credentials.
- The CI battery is intentionally local-backend-friendly and does not require
  live AWS credentials by default.
- Release automation falls back to `GITHUB_TOKEN` when
  `REPO_GITHUB_TOKEN` is not configured.

## Recommended Practices for Downstream Repositories

### Prefer Federated Identity

Use GitHub OIDC with short-lived cloud credentials whenever the target platform
supports it. Static access keys should be treated as an exception for legacy
systems, not the first choice.

### Keep Permissions Narrow

When you add new workflows:

1. start with `contents: read`
2. add only the extra scopes the workflow actually needs
3. document the permission contract in `docs/`

### Review Before Apply

Use `make pulumi-preview` before `make pulumi-up`, and keep reviewable PRs as
the normal path for infrastructure changes. A preview that is not tied to the
code under review is much harder to trust later.

### Prefer Ephemeral Validation Stacks

For manual checks, use short-lived stacks such as `pr-17` or `smoke`, then tear
them down after the test. Shared long-lived development stacks hide drift and
make failure analysis harder.

## Safe Extension Checklist

When you extend this template, verify all of the following:

- new external downloads are pinned and verified
- new workflows define `permissions`, `concurrency`, and `timeout-minutes`
- new Make targets do not print secrets or require live credentials unless that
  behavior is explicitly documented
- new secrets are added to [GitHub Actions Secrets](github-actions-secrets.md)
  and referenced from the relevant operator guide
- structural tests are updated so the security contract stays enforced

## What This Template Intentionally Does Not Do

- It does not auto-deploy infrastructure from pull requests.
- It does not embed long-lived credentials in the Docker image.
- It does not treat CI green status as a replacement for human review of a
  production-impacting infrastructure diff.
