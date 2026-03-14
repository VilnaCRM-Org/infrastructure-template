# Infrastructure Template for Modern DevOps applications

[![SWUbanner](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner2-direct.svg)](https://supportukrainenow.org/)

[![Pulumi Preview](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-preview.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-preview.yml)
[![Pulumi Deploy](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-deploy.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-deploy.yml)
[![Pulumi Unit Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-unit.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-unit.yml)
[![Pulumi Integration Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-integration.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-integration.yml)
[![Pulumi Structural Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-structural.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-structural.yml)
[![Pulumi Mutation Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-mutation.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-mutation.yml)
[![CLI Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/bats-tests.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/bats-tests.yml)
[![Super Linter](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/super-linter.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/super-linter.yml)

Pulumi-first starter repository for teams that want a reproducible AWS infrastructure baseline, a containerized developer workspace, and CI validation before deployments hit a real stack.

## Possibilities

- Pulumi (Python) template that provisions an example EC2 instance through a reusable component and supports preview/deploy workflows.
- Docker Compose workspace with Pulumi, Poetry, AWS CLI, and test tooling preinstalled.
- Focused CI suites for structural, unit, integration, mutation, and CLI-level regression tests.
- Pulumi preview and deploy workflows with GitHub OIDC support and static-key fallback.
- Built-in linting via GitHub Super Linter for repository hygiene.
- Version-controlled documentation under `docs/` instead of wiki-only instructions.

## Why You Might Need It

Bootstrapping infrastructure repositories is repetitive and easy to get wrong. This template gives you:

- A minimal Pulumi stack that is easy to replace with your own resources.
- Local and CI workflows that prove changes before merge.
- Secure-by-default guidance for GitHub Actions, AWS credentials, release automation, and template synchronization.
- A docs-as-code structure that keeps onboarding and operational guidance in-repo.

## License

This software is distributed under the [Creative Commons Zero v1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/deed) license. Please read [`LICENSE`](LICENSE) for details.

## Documentation

All maintained project docs live under `docs/`:

- [Documentation handbook](docs/README.md)
- [Testing and validation matrix](docs/testing.md)
- [GitHub Actions secrets](docs/github-actions-secrets.md)
- [PyCharm autocomplete](docs/pycharm-autocomplete.md)

Community Q&A lives under the [`vilnacrm` tag on Stack Overflow](https://stackoverflow.com/questions/tagged/vilnacrm). For questions or feature requests, open an issue.

## Local Pulumi test suites

Docker Compose CLI 2.24.0+ is required because `docker-compose.yml` uses the `env_file.required` flag.

The Makefile resolves the effective env file as the first existing file from `.env` and `.env.empty`.

- `.env` is git-ignored and should hold local secrets or developer-specific overrides.
- `.env.empty` is committed and acts as the safe fallback for fresh clones and CI jobs.
- `.env.dist` is an optional example file that shows the expected variable names.

Use the `make` targets to validate the repository locally:

```sh
make test-pulumi
make test-unit
make test-integration
make test-mutation
make test-cli
make test
```

## Security

Please disclose vulnerabilities responsibly and report security issues to the maintainers privately. See [`SECURITY.md`](SECURITY.md) and the repository's [security advisories](https://github.com/VilnaCRM-Org/infrastructure-template/security).
