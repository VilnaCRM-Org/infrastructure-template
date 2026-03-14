# Infrastructure Template Documentation

This repository keeps its operational guidance in version-controlled Markdown so template consumers can audit the exact docs that shipped with a given change set.

## Contents

- [Quick Start](#quick-start)
- [Local Tooling](#local-tooling)
- [Testing and Validation](#testing-and-validation)
- [CI/CD and Secrets](#cicd-and-secrets)
- [Project Structure](#project-structure)
- [Repository Synchronization](#repository-synchronization)
- [Security](#security)
- [Contributing](#contributing)

## Quick Start

1. Clone the repository locally or use GitHub's **Use this template** flow.
2. Install Docker Engine/Desktop and Docker Compose CLI 2.24.0+.
3. (Optional) Install the Pulumi CLI if you want to run commands outside the container.
4. Start the local workspace:

   ```bash
   make start
   ```

5. Add local credentials or stack settings in `.env` if you plan to run live previews or deployments.
6. Run the full validation battery before changing the infrastructure stack:

   ```bash
   make test
   ```

## Local Tooling

Most daily workflows are exposed through `make`:

```text
start             Initialize and start the Pulumi development environment.
pulumi-preview    Preview infrastructure changes inside the container.
pulumi-up         Apply the current Pulumi infrastructure plan.
pulumi-refresh    Sync the Pulumi stack with live cloud resources.
pulumi-destroy    Tear down the Pulumi stack.
test-pulumi       Structural validation for manifests, workflows, and supply-chain guards.
test-unit         Pulumi component tests with mocks.
test-integration  Full stack smoke test with Pulumi runtime mocks.
test-mutation     Mutation analysis of the component layer.
test-cli          Bats-based checks for the Makefile interface.
```

For IDE setup, see [PyCharm autocomplete](pycharm-autocomplete.md).

## Testing and Validation

The repository is covered by five complementary test types:

- Structural tests validate Pulumi manifest metadata, CI workflow contracts, and Dockerfile checksum verification.
- Unit tests exercise the `ExampleServer` component directly with Pulumi mocks.
- Integration tests execute the real `pulumi/__main__.py` entrypoint with Pulumi runtime mocks to catch wiring regressions.
- Mutation tests run `mutmut` against the component implementation.
- CLI tests use Bats to lock down the `make` interface.

See the dedicated [testing guide](testing.md) for local commands and CI mapping.

## CI/CD and Secrets

Preview and deploy workflows support GitHub OIDC and static IAM credentials. Test workflows stay local-only and should not require AWS access.

Read [GitHub Actions secrets](github-actions-secrets.md) before configuring repository credentials.

## Project Structure

- `pulumi/` contains the Pulumi program and reusable component code.
- `tests/` contains structural, unit, integration, and CLI tests.
- `docs/` contains operational and onboarding documentation.
- `.github/workflows/` contains CI, deployment, release, and template-sync workflows.

## Repository Synchronization

This template is synchronized into downstream repositories through [`actions-template-sync`](https://github.com/AndreasAugustin/actions-template-sync). Existing guidance for PAT- and GitHub App-based sync remains in `.github/TEMPLATE_SYNC_PAT.md` and `.github/TEMPLATE_SYNC_APP.md`.

## Security

Report security issues responsibly to the maintainers. See [`SECURITY.md`](../SECURITY.md) and the repository's [security advisories](https://github.com/VilnaCRM-Org/infrastructure-template/security).

## Contributing

Pull requests should update `docs/` whenever the developer workflow, CI surface, or credential expectations change. The main contribution flow lives in [`CONTRIBUTING.md`](../CONTRIBUTING.md).
