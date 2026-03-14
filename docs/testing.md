# Testing and Validation

This repository uses multiple test types so infrastructure-template changes are checked from configuration shape down to the developer CLI surface.

Run `make doctor` first if you suspect the problem is your local Docker or
Compose setup rather than the repository itself.

## Structural tests

Run with:

```bash
make test-pulumi
```

Coverage:

- Every public Make target is exercised through dry-run or help-output assertions
- `pulumi/Pulumi.yaml`
- Release workflow contracts
- Dockerfile supply-chain safeguards

## Quality checks

Run with:

```bash
make test-quality
```

Coverage:

- `ruff check` for fast linting
- `ruff format --check` for formatting drift
- `ty check` for static typing diagnostics on the Pulumi application layer

Ty currently ignores a small set of false positives caused by Pulumi's dynamic
`Output.apply` API and the coverage bootstrap shim. The CI command keeps those
exceptions explicit instead of silently disabling the type check.

## Unit tests

Run with:

```bash
make test-unit
```

Coverage:

- `pulumi/app/environment.py`
- Config fallback behavior for `environment` and `serviceName`
- Component type token and exported outputs

## Integration tests

Run with:

```bash
make test-integration
```

Coverage:

- The real `pulumi/__main__.py` entrypoint
- Pulumi Automation lifecycle behavior with a local backend
- Output wiring for environment metadata

The Docker workspace keeps its `uv` virtual environment outside the bind-mounted
repository tree so Pulumi always sees a stable interpreter with `pip`
available for plugin discovery.

## Mutation tests

Run with:

```bash
make test-mutation
```

Coverage:

- Mutation analysis of `pulumi/app`
- Regression resistance for unit and integration assertions

Mutation testing is the slowest suite and is usually best left to CI unless you are changing component logic directly.

## CLI tests

Run with:

```bash
make test-cli
```

Coverage:

- `make help`
- `make all`
- `make start`
- `make pulumi-preview`
- `make pulumi-up`
- `make pulumi-refresh`
- `make pulumi-destroy`
- `make sh`
- `make down`
- `make test-unit`
- `make test-integration`
- `make test-pulumi`
- `make test-quality`
- `make test-ruff`
- `make test-ty`
- `make test-mutation`
- `make test-cli`
- `make test`
- `make clean`

## Full local run

Run the standard local validation battery with:

```bash
make test
make ci-pr
make ci
```

Use `make test` during normal iteration when you want the fast structural, quality, unit, integration, and CLI suites after a prerequisite sanity check. Use `make ci-pr` when you want the same non-mutation battery that GitHub runs in `pulumi-local.yml`. Use `make ci` before pushing when you want the full local equivalent of every GitHub check, including the prerequisite check, Docker build, and mutation suite.

GitHub Actions now mirrors `make ci-pr` through the `Pulumi Local Test Battery` workflow, while `Pulumi Mutation Tests` keeps mutation analysis isolated as a separate check.
The `Python Quality Checks` workflow runs Ruff and Ty as dedicated quality gates.

Use `make pulumi-preview` before any real cloud deployment.
