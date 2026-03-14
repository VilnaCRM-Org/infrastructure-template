# Infrastructure Template Documentation

We follow a docs-as-code workflow: every guide lives alongside the source and evolves through pull requests. Update or add files in this folder whenever you change the infrastructure template so future readers stay aligned with the repository.

## Contents

- [Quick Start](#quick-start)
- [Local Tooling](#local-tooling)
- [Development](#development)
- [Python Tooling](#python-tooling)
- [CI/CD and Secrets](#cicd-and-secrets)
- [CI Architecture](#ci-architecture)
- [Pulumi Guardrails](#pulumi-guardrails)
- [Security Baseline](#security-baseline)
- [Project Structure](#project-structure)
- [Testing and Validation](#testing-and-validation)
- [SRE Operations](#sre-operations)
- [Detailed Test Matrix](#detailed-test-matrix)
- [Repository Synchronization](#repository-synchronization)
- [Security](#security)
- [Contributing](#contributing)
- [Sponsorship](#sponsorship)
- [Documentation Workflow](#documentation-workflow)

## Quick Start

1. **Use this template** or clone the repository locally.
2. Install [Docker](https://docs.docker.com/engine/install/) and [Docker Compose](https://docs.docker.com/compose/install/)
   (Docker Compose CLI 2.24.0+ is required because `docker-compose.yml` uses
   `env_file.required`).
3. (Optional) Install the [Pulumi CLI](https://www.pulumi.com/docs/install/) if you plan to run commands outside the container.
4. Launch the local environment:

   ```bash
   make start
   ```

5. Configure your AWS credentials (for example via `aws configure`, environment variables, or GitHub Actions secrets).
6. Run a preview from inside the container to validate infrastructure changes:

   ```bash
   make pulumi-preview
   ```

That is all you need to begin iterating on the sample AWS instance or adapting the stack to your own infrastructure.

## Local Tooling

`make help` prints the available tasks. Most common targets:

```text
all               Display help (default goal).
build             Build the Pulumi development image used by local and CI checks.
ci                Run the full local equivalent of all GitHub checks, including mutation.
ci-pr             Run the non-mutation GitHub pull-request battery locally.
doctor            Check local prerequisites and effective paths without printing secrets.
help              Print the available make targets.
start             Initialize and start the Pulumi development environment.
pulumi-preview    Preview infrastructure changes with the policy pack enforced.
pulumi-up         Apply the current infrastructure plan with the policy pack enforced.
pulumi-refresh    Sync the Pulumi stack with live cloud resources.
pulumi-destroy    Tear down the stack (irreversible; use with caution).
sh                Open a shell inside the Pulumi container.
down              Stop the Docker Compose environment.
test              Run the aggregate structural, quality, unit, integration, and CLI battery.
test-pulumi       Structural validation for manifests, workflows, and supply-chain guards.
test-policy       Pulumi policy-pack tests and guardrail coverage.
test-quality      Rust-based linting, formatting, and typing checks.
test-ruff         Ruff lint and format drift checks.
test-ty           Ty static typing diagnostics for the Pulumi layer.
test-unit         Pulumi component tests with mocks.
test-integration  Pulumi Automation smoke tests with a local backend.
test-mutation     Mutation analysis of the component layer.
test-cli          Bats-based checks for the Makefile interface.
clean             Remove Docker Compose artifacts and Python build caches.
```

## Development

We recommend editing the project through the Docker workspace so IDEs can reuse
the interpreter that already ships with the repository (Pulumi CLI, Python SDKs,
uv, Ruff, Ty).

- [PyCharm autocomplete guide](pycharm-autocomplete.md) — shows how to attach
  PyCharm to the Docker Compose interpreter or create a local virtualenv
  fallback.
- `docker compose up --build -d` launches the workspace; `docker compose down`
  stops it.

## Python Tooling

The repository now uses `uv` for locking, syncing, and command execution, with
Ruff and Ty as fast Rust-based quality gates.

- The Docker workspace keeps its `uv` environment outside the bind-mounted
  workspace so host mounts cannot replace the interpreter seen by Pulumi
  (see `docker-compose.yml` for the canonical workspace layout).
- If you want a local virtual environment outside Docker, seed it once before
  syncing:

  ```bash
  export UV_PROJECT_ENVIRONMENT="${HOME}/.venvs/infrastructure-template"
  uv venv --seed "${UV_PROJECT_ENVIRONMENT}"
  uv sync --all-groups
  ```

- The detailed workflow and rationale live in
  [uv and Rust-native Python tooling](uv-rust-python-tooling-plan.md).

## CI/CD and Secrets

CI checks are split into focused workflows that run inside the Docker workspace:

- `pulumi-structural.yml` validates Pulumi project metadata.
- `pulumi-unit.yml` runs unit tests with Pulumi mocks.
- `pulumi-integration.yml` runs Pulumi Automation tests with a local file backend.
- `pulumi-policy.yml` executes the Pulumi policy-pack suite.
- `pulumi-mutation.yml` executes mutation testing.
- `python-quality.yml` runs Ruff and Ty as dedicated quality checks.
- `bats-tests.yml` validates the Makefile CLI surface.
- `pulumi-local.yml` runs `make ci-pr`, the non-mutation pull-request battery inside Docker.

These checks do not require AWS or Pulumi credentials by default. They use
concurrency groups, bounded job timeouts, pinned actions, and a shared
`./scripts/prepare_docker_context.sh` bootstrap path so local and GitHub-hosted
validation stay aligned. If you add deploy workflows or provision real cloud
resources, follow the [GitHub Actions Secrets guide](github-actions-secrets.md)
to configure the required secrets.

## CI Architecture

Use the dedicated [CI architecture guide](ci-architecture.md) when you need the
workflow matrix, local-to-GitHub mapping, or the checklist for adding a new CI
job safely.

## Security Baseline

Use the [security baseline](security-baseline.md) for the template's enforced
controls, extension checklist, and guidance on secrets, token scope, and
supply-chain hygiene.

## Pulumi Guardrails

Use the [Pulumi guardrails guide](pulumi-guardrails.md) for the runtime
identifier rules, policy-pack guardrails, and the local/CI commands that keep
them enforced.

## Project Structure

- `pulumi/__main__.py` – Minimal Pulumi program that exports environment metadata and tags.
- `docker-compose.yml` – Local development environment with Pulumi tooling baked in.
- `Makefile` – Convenience commands for preview, testing, and container management.
- `.github/workflows` – Automation for CI checks, releases, and template synchronization.

## Testing and Validation

Continuous integration runs automatically on every pull request. You can also validate locally:

- Start with `make doctor` if you need a quick sanity check of Docker, Compose, and the effective env file.
- Use the focused suites when you only need one slice: `make build`, `make test-pulumi`, `make test-policy`, `make test-quality`, `make test-unit`, `make test-integration`, `make test-mutation`, `make test-cli`.
- Use `make test-policy` when you are changing guardrails or adding new AWS resource types that should be covered by the policy pack.
- `make pulumi-preview` and `make pulumi-up` sync the shared `uv` environment if needed and then run Pulumi with the repository policy pack enabled.
- Run `make test` to execute the faster structural, quality, unit, integration, and CLI checks together after a prerequisite sanity check.
- Execute `make ci-pr` to mirror the non-mutation GitHub pull-request battery, including the prerequisite check, image build, and policy suite.
- Execute `make ci` to run the full local equivalent of all GitHub checks, including the prerequisite check, image build, and mutation suite.
- `make pulumi-preview` to review planned resources before applying.
- `make pulumi-up` followed by `pulumi stack output` to inspect applied results.
- GitHub Actions mirrors `make ci-pr` through the `Pulumi Local Test Battery` workflow, while mutation remains isolated in `pulumi-mutation.yml`.

## SRE Operations

Use the [SRE operations guide](sre-operations.md) for preview/apply/refresh
flows, stack strategy, failure triage, release hygiene, and cleanup guidance.

## Detailed Test Matrix

Use the dedicated [testing guide](testing.md) when you need to know exactly what each suite covers or which local command maps to which CI workflow.

## Repository Synchronization

This template feeds other VilnaCRM infrastructure projects through [`actions-template-sync`](https://github.com/AndreasAugustin/actions-template-sync). For authentication guidance, see the [Template Sync secrets](github-actions-secrets.md#template-sync-secrets).

Remember to grant least privilege, rotate secrets regularly, and monitor workflow logs.

## Security

Report security issues responsibly to the maintainers. Consult [`SECURITY.md`](../SECURITY.md) and the repository’s [security advisories](https://github.com/VilnaCRM-Org/infrastructure-template/security).

## Contributing

Bug reports, feature requests, and pull requests are welcome via the [issue tracker](https://github.com/VilnaCRM-Org/infrastructure-template/issues). Documentation updates are highly appreciated—edit the files under `docs/` so improvements travel with the code.

## Sponsorship

Development time and resources for this repository are provided by [VilnaCRM](https://vilnacrm.com/), the free and open-source CRM system.

Donations are very welcome, whether in beer 🍺, T-shirts 👕, or cold, hard cash 💰. Sponsorship through GitHub is a simple and convenient way to say "thank you" to maintainers and contributors – just click the "Sponsor" button [on the project page](https://github.com/VilnaCRM-Org/infrastructure-template). If your company uses this template, consider taking part in the VilnaCRM's enterprise support program.

## Documentation Workflow

1. Add or edit Markdown inside `docs/`.
2. Cross-link the new material from `README.md` or other docs so it is discoverable.
3. Include documentation updates in the same PR as related code changes whenever possible.
4. Keep `AGENTS.md` aligned with any workflow or secret-handling changes that affect coding agents.

You can organize content as it grows by creating subdirectories (e.g., `docs/pulumi/`).
