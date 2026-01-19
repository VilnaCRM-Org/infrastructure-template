# Infrastructure Template for Modern DevOps applications

[![SWUbanner](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner2-direct.svg)](https://supportukrainenow.org/)

[![Pulumi Unit Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-unit.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-unit.yml)
[![Pulumi Integration Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-integration.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-integration.yml)
[![Pulumi Structural Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-structural.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-structural.yml)
[![Pulumi Mutation Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-mutation.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-mutation.yml)
[![CLI Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/bats-tests.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/bats-tests.yml)

Production-ready scaffold for teams that want to ship infrastructure-as-code with Pulumi and Docker from day zero.

## Possibilities

- Pulumi (Python) starter that exports environment metadata and tagging helpers.
- Reproducible Docker Compose workspace with a Pulumi-ready container and helper `make` tasks.
- CI pipelines for structural, unit, integration, mutation, and CLI-level checks.
- Release and template-sync automations to keep downstream repos aligned.
- Documentation on AWS credential management for secure automation using GitHub OIDC or static secrets.

## Why You Might Need It

Spin up consistent project infrastructure without wiring every component manually. This template gives DevOps teams a single source that:

- Encodes best practices from VilnaCRM’s production stack.
- Works out-of-the-box with AWS and Pulumi.
- Keeps infrastructure changes reviewable with local Pulumi previews and CI test suites before deploying.

## License

This software is distributed under the [Creative Commons Zero v1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/deed) license. Please read [`LICENSE`](LICENSE) for details.

## Documentation

All project docs live under `docs/` to keep everything version controlled. Start with the handbook and jump directly to common topics:

- [Quick Start](docs/README.md#quick-start)
- [Local Tooling](docs/README.md#local-tooling)
- [Development Environment](docs/README.md#development)
- [PyCharm Autocomplete](docs/pycharm-autocomplete.md)
- [CI/CD and Secrets](docs/README.md#cicd-and-secrets)
- [Testing and Validation](docs/README.md#testing-and-validation)
- [Security](docs/README.md#security)
- [Contributing](docs/README.md#contributing)
- [Sponsorship](docs/README.md#sponsorship)

Community Q&A lives under the [`vilnacrm` tag on Stack Overflow](https://stackoverflow.com/questions/tagged/vilnacrm). For questions or feature requests, open an issue.

## Local Pulumi test suites

Install development dependencies via Poetry and then use the `make` targets to run the different Pulumi-focused suites:

```sh
poetry install --with dev

# Configuration validation
make test-pulumi

# Unit tests (pure Pulumi runtime with mocks)
make test-unit

# Automation-based integration tests
make test-integration

# Mutation analysis (time-consuming)
make test-mutation
```

You can also execute `make test` to run the structural, unit, and integration checks as a batch.

## Security

Please disclose any vulnerabilities found responsibly – report security issues to the maintainers privately.
