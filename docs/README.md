# Infrastructure Template Documentation

We follow a docs-as-code workflow: every guide lives alongside the source and evolves through pull requests. Update or add files in this folder whenever you change the infrastructure template so future readers stay aligned with the repository.

## Contents

- [Quick Start](#quick-start)
- [Local Tooling](#local-tooling)
- [Development](#development)
- [CI/CD and Secrets](#cicd-and-secrets)
- [Project Structure](#project-structure)
- [Testing and Validation](#testing-and-validation)
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
help              Print the available make targets.
start             Initialize and start the Pulumi development environment.
pulumi-preview    Preview infrastructure changes from inside the container.
pulumi-up         Apply the current infrastructure plan.
pulumi-refresh    Sync the Pulumi stack with live cloud resources.
pulumi-destroy    Tear down the stack (irreversible; use with caution).
sh                Open a shell inside the Pulumi container.
down              Stop the Docker Compose environment.
test              Run the aggregate structural, unit, integration, and CLI battery.
test-pulumi       Structural validation for manifests, workflows, and supply-chain guards.
test-unit         Pulumi component tests with mocks.
test-integration  Pulumi Automation smoke tests with a local backend.
test-mutation     Mutation analysis of the component layer.
test-cli          Bats-based checks for the Makefile interface.
clean             Remove Docker Compose artifacts and Python build caches.
```

## Development

We recommend editing the project through the Docker workspace so IDEs can reuse
the interpreter that already ships with the repository (Pulumi CLI, Python SDKs,
Black, Flake8, Pre-commit).

- [PyCharm autocomplete guide](pycharm-autocomplete.md) — shows how to attach
  PyCharm to the Docker Compose interpreter or create a local virtualenv
  fallback.
- `docker compose up --build -d` launches the workspace; `docker compose down`
  stops it.

## CI/CD and Secrets

CI checks are split into focused workflows that run inside the Docker workspace:

- `pulumi-structural.yml` validates Pulumi project metadata.
- `pulumi-unit.yml` runs unit tests with Pulumi mocks.
- `pulumi-integration.yml` runs Pulumi Automation tests with a local file backend.
- `pulumi-mutation.yml` executes mutation testing.
- `bats-tests.yml` validates the Makefile CLI surface.

These checks do not require AWS or Pulumi credentials by default. The `pulumi-local.yml` workflow also reruns the aggregate `make test` battery used during local development. If you add deploy workflows or provision real cloud resources, follow the [GitHub Actions Secrets guide](github-actions-secrets.md) to configure the required secrets.

## Project Structure

- `pulumi/__main__.py` – Minimal Pulumi program that exports environment metadata and tags.
- `docker-compose.yml` – Local development environment with Pulumi tooling baked in.
- `Makefile` – Convenience commands for preview, testing, and container management.
- `.github/workflows` – Automation for CI checks, releases, and template synchronization.

## Testing and Validation

Continuous integration runs automatically on every pull request. You can also validate locally:

- `make test-pulumi`, `make test-unit`, `make test-integration`, `make test-mutation`, `make test-cli` for focused suites.
- `make test` to run the structural, unit, integration, and CLI checks together.
- `make pulumi-preview` to review planned resources before applying.
- `make pulumi-up` followed by `pulumi stack output` to inspect applied results.
- GitHub Actions mirrors the aggregate `make test` command through the `Pulumi Local Test Battery` workflow.

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
