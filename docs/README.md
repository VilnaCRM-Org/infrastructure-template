# Infrastructure Template Documentation

This repository keeps its operational guidance in version-controlled Markdown so template consumers can audit the exact docs that shipped with a given change set. We follow a docs-as-code workflow: update or add files in this folder whenever you change the infrastructure template so future readers stay aligned with the repository.

## Contents

- [Quick Start](#quick-start)
- [Local Tooling](#local-tooling)
- [Development](#development)
- [CI/CD and Secrets](#cicd-and-secrets)
- [Project Structure](#project-structure)
- [Testing and Validation](#testing-and-validation)
- [Repository Synchronization](#repository-synchronization)
- [Security](#security)
- [Contributing](#contributing)
- [Documentation Workflow](#documentation-workflow)

## Quick Start

1. Use GitHub's **Use this template** flow or clone the repository locally.
2. Install Docker Engine/Desktop and Docker Compose CLI 2.24.0+.
3. (Optional) Install the Pulumi CLI if you want to run commands outside the container.
4. Start the local workspace:

   ```bash
   make start
   ```

5. Add local credentials or stack settings in `.env` if you plan to run live previews or deployments. Fresh clones can rely on `.env.empty` for local-only validation.
6. Run the full validation battery before opening a pull request:

   ```bash
   make test
   ```

7. Use `make pulumi-preview` when you want to validate infrastructure changes against a live stack.

## Local Tooling

Most daily workflows are exposed through `make`:

```text
all               Display help (default goal).
help              Print the available make targets.
start             Initialize and start the Pulumi development environment.
pulumi            Proxy arbitrary Pulumi CLI commands.
pulumi-preview    Preview infrastructure changes inside the container.
pulumi-up         Apply the current Pulumi infrastructure plan.
pulumi-refresh    Sync the Pulumi stack with live cloud resources.
pulumi-destroy    Tear down the Pulumi stack.
sh                Open a shell inside the Pulumi container.
down              Stop the Docker Compose environment.
test              Run the aggregate structural, unit, integration, and CLI battery.
test-pulumi       Structural validation for manifests, workflows, and supply-chain guards.
test-unit         Pulumi component tests with mocks.
test-integration  Full stack smoke test with Pulumi runtime mocks.
test-mutation     Mutation analysis of the component layer.
test-cli          Bats-based checks for the Makefile interface.
clean             Remove Docker Compose artifacts and Python build caches.
```

## Development

We recommend editing the project through the Docker workspace so IDEs can reuse the interpreter and tooling that already ship with the repository.

- [PyCharm autocomplete guide](pycharm-autocomplete.md) explains how to attach PyCharm to the Docker Compose interpreter or create a local virtualenv fallback.
- `docker compose up --build -d` launches the workspace.
- `docker compose down` stops it.

## CI/CD and Secrets

The repository uses two cloud-facing workflows and six local-only validation checks:

- `pulumi-preview.yml` evaluates Pulumi changes on pull requests.
- `pulumi-deploy.yml` applies the `dev` stack from `main`.
- `pulumi-local.yml` reruns the aggregate `make test` battery used during local development.
- Structural, unit, integration, mutation, and CLI workflows run without cloud credentials.

Preview and deploy workflows support GitHub OIDC and static IAM credentials. Read [GitHub Actions secrets](github-actions-secrets.md) before configuring repository credentials.
When the repository has no cloud credentials configured, those workflows skip cleanly after a preflight check so template pull requests can still validate the local-only suites.

## Project Structure

- `pulumi/` contains the Pulumi program and reusable component code.
- `tests/` contains structural, unit, integration, mutation, and CLI tests.
- `docs/` contains operational and onboarding documentation.
- `.github/workflows/` contains CI, deployment, release, and template-sync workflows.
- `Makefile` is the main entrypoint for local developer workflows.

## Testing and Validation

The repository is covered by five complementary test types plus an aggregate local-battery workflow:

- Structural tests validate Pulumi manifest metadata, CI workflow contracts, and Dockerfile checksum verification.
- Unit tests exercise the `ExampleServer` component directly with Pulumi mocks.
- Integration tests execute the real `pulumi/__main__.py` entrypoint with Pulumi runtime mocks to catch wiring regressions.
- Mutation tests run `mutmut` against the component implementation.
- CLI tests use Bats to lock down every public `make` target.
- The `Pulumi Local Test Battery` workflow runs `make test` in CI so the aggregate local command stays aligned with the individual checks.

See the dedicated [testing guide](testing.md) for local commands, CI mapping, and expected coverage.

## Repository Synchronization

This template is synchronized into downstream repositories through [`actions-template-sync`](https://github.com/AndreasAugustin/actions-template-sync). Authentication guidance remains in:

- `.github/TEMPLATE_SYNC_PAT.md` for Personal Access Tokens.
- `.github/TEMPLATE_SYNC_APP.md` for GitHub App credentials.

## Security

Report security issues responsibly to the maintainers. See [`SECURITY.md`](../SECURITY.md) and the repository's [security advisories](https://github.com/VilnaCRM-Org/infrastructure-template/security).

## Contributing

Pull requests should update `docs/` whenever the developer workflow, CI surface, or credential expectations change. The main contribution flow lives in [`CONTRIBUTING.md`](../CONTRIBUTING.md).

## Documentation Workflow

1. Add or edit Markdown inside `docs/`.
2. Cross-link the new material from `README.md` or other docs so it is discoverable.
3. Update [`AGENTS.md`](../AGENTS.md) alongside docs when the repository workflow for agents or reviewers changes.
4. Include documentation updates in the same pull request as related code changes whenever possible.
