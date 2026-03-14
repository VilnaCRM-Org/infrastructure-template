# CI Architecture

This repository keeps CI intentionally close to the local developer workflow.
Every pull request check is driven by the same Docker workspace and the same
`make` entrypoints that developers use locally.

## Design Principles

- local/CI parity over bespoke workflow-only commands
- short feedback loops for structural and unit checks
- explicit isolation for slower suites such as mutation testing
- safe defaults: least privilege, cancellable duplicates, bounded run time

## Workflow Matrix

| Workflow | Primary command | Purpose |
| --- | --- | --- |
| `pulumi-structural.yml` | `make test-pulumi` | Validates Pulumi metadata, workflow contracts, and Dockerfile safeguards |
| `python-quality.yml` | `make test-ruff`, `make test-ty` | Fast Rust-based linting, formatting, and type diagnostics |
| `pulumi-unit.yml` | `make test-unit` | Mock-based Pulumi component tests with full coverage |
| `pulumi-integration.yml` | `make test-integration` | Automation API lifecycle tests against a local file backend |
| `pulumi-mutation.yml` | `make test-mutation` | Mutation analysis of the Pulumi component layer |
| `bats-tests.yml` | `make test-cli` | CLI contract tests for the Makefile interface |
| `pulumi-local.yml` | `make ci` | Full PR-equivalent battery inside Docker |

## Shared Controls

### Prepared Docker Context

CI workflows call `./scripts/prepare_docker_context.sh` before running checks.
That script standardizes the expected local state:

- creates `${HOME}/.aws` with restrictive permissions
- materializes `.env` from `.env.empty` when needed
- prepares the `.pulumi-backend` directory used by local-backend test flows

Centralizing the setup keeps workflows consistent and reduces drift between
checks.

### Concurrency

Every pull-request-oriented validation workflow uses a concurrency group based on
the workflow name and PR number or ref. That prevents multiple stale runs from
contending on the same branch after rapid pushes.

### Timeouts

Every CI job declares `timeout-minutes`. Fast suites fail fast; slower suites
such as mutation testing and the full local battery are allowed more time but
still remain bounded.

### Minimal Permissions

Validation workflows use `contents: read`. Release and synchronization workflows
ask for broader access only where automation actually needs to write tags,
releases, or pull requests.

## Local Parity

The repository intentionally avoids workflow-only logic for the core validation
battery.

- `make test` is the fast inner-loop command.
- `make ci` is the full local equivalent of the pull-request battery.
- `make doctor` provides a quick prerequisite check before developers start
  debugging Docker or Pulumi behavior.

If you add a new CI check, prefer adding a Make target first and making GitHub
Actions call that target.

## Adding a New Workflow

Use this checklist:

1. add or reuse a Make target
2. keep the workflow on pinned actions
3. define `permissions`
4. add `concurrency`
5. set `timeout-minutes`
6. reuse `./scripts/prepare_docker_context.sh` if the job uses the Docker
   workspace
7. extend the structural tests and docs in the same PR

## Failure Triage

When a PR check fails:

1. reproduce with the matching local Make target
2. run `make doctor` if the failure looks environment-related
3. inspect the workflow job log only after the local path is understood
4. fix the underlying contract rather than weakening the check
