# Testing and Validation

This repository intentionally splits validation into narrow suites so failures point to the exact layer that regressed.

## Structural tests

Run with:

```bash
make test-pulumi
```

Coverage:

- Every public Make target is exercised through dry-run or help-output assertions
- `pulumi/Pulumi.yaml` and `pulumi/Pulumi.example.yaml`
- GitHub Actions workflow contracts for preview, deploy, and linting
- Dockerfile checksum and pinned-download safeguards

## Unit tests

Run with:

```bash
make test-unit
```

Coverage:

- `pulumi/app/server.py`
- Config fallback behavior for `amiId`, `instanceType`, and `nameTag`
- Component type token and exported Pulumi outputs

These tests use Pulumi mocks, so they do not require AWS credentials.

## Integration smoke tests

Run with:

```bash
make test-integration
```

Coverage:

- The real `pulumi/__main__.py` entrypoint
- Composition between the stack entrypoint and the `ExampleServer` component
- Output wiring for the EC2 instance metadata

This suite still uses Pulumi runtime mocks to stay deterministic in CI.

## Mutation tests

Run with:

```bash
make test-mutation
```

Coverage:

- Mutation analysis of `pulumi/app/server.py`
- Regression resistance for both unit and integration-smoke assertions

Mutation testing is the slowest suite and is best left to CI unless you are working directly on the component behavior.

## CLI tests

Run with:

```bash
make test-cli
```

Coverage:

- `make help`
- `make all`
- `make start`
- `make pulumi ARGS="version"`
- `make pulumi-preview`
- `make pulumi-up`
- `make pulumi-refresh`
- `make pulumi-destroy`
- `make sh`
- `make down`
- `make test-unit`
- `make test-integration`
- `make test-pulumi`
- `make test-mutation`
- `make test-cli`
- `make test`
- `make clean`

These tests use dry-run output, so they do not require Docker to launch real containers.

## Full local run

Run the complete local validation battery with:

```bash
make test
make test-mutation
```

GitHub Actions now mirrors the aggregate `make test` command through the `Pulumi Local Test Battery` workflow, while `Pulumi Mutation Tests` keeps mutation analysis isolated as a separate check.

Use `make pulumi-preview` before any real cloud deployment.
