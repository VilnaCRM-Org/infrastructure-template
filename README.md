# Infrastructure Template for Modern DevOps applications

[![SWUbanner](https://raw.githubusercontent.com/vshymanskyy/StandWithUkraine/main/banner2-direct.svg)](https://supportukrainenow.org/)

[![Pulumi Unit Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-unit.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-unit.yml)
[![Pulumi Integration Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-integration.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-integration.yml)
[![Pulumi Structural Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-structural.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-structural.yml)
[![Pulumi Policy Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-policy.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-policy.yml)
[![Pulumi Mutation Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-mutation.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/pulumi-mutation.yml)
[![CLI Tests](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/bats-tests.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/bats-tests.yml)
[![Python Quality Checks](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/python-quality.yml/badge.svg)](https://github.com/VilnaCRM-Org/infrastructure-template/actions/workflows/python-quality.yml)

Production-ready scaffold for teams that want to ship infrastructure-as-code with Pulumi and Docker from day zero.

## Possibilities

- Pulumi (Python) starter that exports environment metadata and tagging helpers.
- Reproducible Docker Compose workspace with a Pulumi-ready container and helper `make` tasks.
- CI pipelines for structural, policy, unit, integration, mutation, and CLI-level checks.
- Release and template-sync automations to keep downstream repos aligned.
- Documentation on AWS credential management for secure automation using GitHub OIDC or static secrets.

## Why You Might Need It

Spin up consistent project infrastructure without wiring every component manually. This template gives DevOps teams a single source that:

- Encodes best practices from VilnaCRM’s production stack.
- Works out-of-the-box with AWS and Pulumi.
- Keeps infrastructure changes reviewable with local Pulumi previews, policy-pack guardrails, and CI test suites before deploying.

## License

This software is distributed under the [Creative Commons Zero v1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/deed) license. Please read [`LICENSE`](LICENSE) for details.

## Documentation

All project docs live under `docs/` to keep everything version controlled. Start with the handbook and jump directly to common topics:

- [Quick Start](docs/README.md#quick-start)
- [Local Tooling](docs/README.md#local-tooling)
- [Development Environment](docs/README.md#development)
- [PyCharm Autocomplete](docs/pycharm-autocomplete.md)
- [CI/CD and Secrets](docs/README.md#cicd-and-secrets)
- [CI Architecture](docs/ci-architecture.md)
- [Security Baseline](docs/security-baseline.md)
- [Pulumi Guardrails](docs/pulumi-guardrails.md)
- [uv and Rust-native Python tooling](docs/uv-rust-python-tooling-plan.md)
- [SRE Operations](docs/sre-operations.md)
- [Testing and Validation](docs/README.md#testing-and-validation)
- [Security](docs/README.md#security)
- [Contributing](docs/README.md#contributing)
- [Sponsorship](docs/README.md#sponsorship)

Community Q&A lives under the [`vilnacrm` tag on Stack Overflow](https://stackoverflow.com/questions/tagged/vilnacrm). For questions or feature requests, open an issue.

## Local Pulumi test suites

Docker Compose CLI 2.24.0+ is required because `docker-compose.yml` uses the
`env_file.required` flag (older Compose releases fail to parse it).

## Environment files

The Makefile resolves the effective env file as the first existing file from
`.env` and `.env.empty`.

- `.env` is git-ignored and should hold local secrets or developer-specific overrides.
- `.env.empty` is committed and acts as the minimal fallback so Docker Compose and `make` targets still run in a fresh clone.
- `.env.dist` remains an optional example/template file you can copy from when you want a fuller starting point; unlike `.env.empty`, it is not the automatic fallback used by the Makefile.

For onboarding, create or update `.env` with any local overrides you need, keep
`.env.empty` safe to commit, and refresh `.env.dist` only when the example
values or documented setup flow changes.

If you want a local `uv` environment outside Docker, seed it once so Pulumi's
Automation API can still use `pip` for package discovery:

```sh
export UV_PROJECT_ENVIRONMENT="${HOME}/.venvs/infrastructure-template"
uv venv --seed "${UV_PROJECT_ENVIRONMENT}"
uv sync --all-groups
```

The Docker workspace already ships with an isolated seeded environment outside
the bind-mounted repository tree, so the `make` targets remain the recommended
way to run the different Pulumi-focused suites (see `docker-compose.yml` for
the canonical workspace layout):

```sh
# Build the dev image used by the local and CI batteries
make build

# Configuration validation
make test-pulumi

# Rust-based quality gates
make test-quality

# Pulumi policy and guardrail validation
make test-policy

# Unit tests (pure Pulumi runtime with mocks)
make test-unit

# Automation-based integration tests
make test-integration

# Mutation analysis (time-consuming)
make test-mutation
```

Use `make test` for the faster structural, policy, quality, unit, integration, and CLI battery during day-to-day development. Use `make ci-pr` when you want the same non-mutation battery that GitHub runs in `pulumi-local.yml`. Use `make ci` when you want the full local superset, including the prerequisite check, image build, and mutation suite.

Run `make doctor` when you need a fast prerequisite check before debugging local
Docker or Compose behavior.

`make pulumi-preview` and `make pulumi-up` automatically enable the repository
policy pack. If the shared `uv` environment inside the container is missing the
policy runtime dependencies, the bootstrap helper resyncs it from `uv.lock`
before Pulumi starts.

## Security

Please disclose any vulnerabilities found responsibly – report security issues to the maintainers privately.
