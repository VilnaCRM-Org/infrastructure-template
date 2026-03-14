# uv and Rust-Native Python Tooling Roadmap

This document captures the implementation plan for [issue #16](https://github.com/VilnaCRM-Org/infrastructure-template/issues/16).

The repository `main` branch still reflects the Terraform/Terraspace template. The scope below is a follow-up to the Pulumi/Python migration work currently under review. Once that work lands, this repository should modernize the Python toolchain further by replacing Poetry with `uv` and by adding Rust-based quality tooling to CI.

## Goals

- Replace Poetry with `uv` for dependency resolution, locking, and command execution.
- Keep local development, Docker workflows, and GitHub Actions aligned around one Python workflow.
- Add fast Rust-based quality gates that improve signal without making the contributor experience worse.

## Proposed Tooling

### uv

Use `uv` as the primary package and environment manager:

- `uv sync` for dependency installation.
- `uv run` for command execution in local workflows, Docker, and CI.
- `uv lock` to maintain `uv.lock`.

### Ruff

Add `ruff` as a required CI check:

- `ruff check` for linting.
- `ruff format --check` for formatting.

Ruff is mature, fast, and a practical replacement for slower Python-only lint/format stacks.

### Ty

Evaluate `ty check` for static typing after the `uv` migration is in place.

- If it produces actionable signal with acceptable noise, add it to CI.
- If it is still too immature for this repository, document that decision explicitly and defer it instead of carrying an unreliable required check.

## Planned Workstreams

### 1. Packaging and Locking

- Convert the Pulumi/Python `pyproject.toml` away from Poetry metadata.
- Replace Poetry lock usage with `uv.lock`.
- Update contributor commands so the repository consistently documents `uv sync` and `uv run`.

### 2. Local Tooling and Docker

- Replace Poetry installation in the Docker image with `uv`.
- Update `Makefile` targets to call `uv run` where Python tools are executed.
- Refresh shell examples and troubleshooting guidance in `README.md`, `docs/README.md`, `docs/testing.md`, and `AGENTS.md`.

### 3. CI Quality Gates

- Update GitHub Actions to install and cache `uv`.
- Remove Poetry-specific setup from all Pulumi/Python workflows.
- Add dedicated CI checks for Ruff.
- Evaluate Ty and either add it as a check or document a deferral with reasons.

### 4. Test Coverage

- Update structural tests so they assert the `uv` workflow contract.
- Update Bats tests for `make` targets if command output changes.
- Refresh any unit or integration tests that currently assume Poetry-specific paths or commands.

## Definition of Done

- Poetry is fully removed from the active Python workflow introduced by the Pulumi migration.
- `uv.lock` is committed and used in CI and local development.
- Rust-based quality checks are wired into GitHub Actions and documented.
- The repository documentation under `docs/` reflects the final workflow.
- All required GitHub checks are green on the implementation PR.
