# Testing and Validation

This repository uses multiple test types so infrastructure-template changes are checked from configuration shape down to the developer CLI surface.

## Structural tests

Run with:

```bash
make test-pulumi
```

Coverage:

- `pulumi/Pulumi.yaml`
- Release workflow contracts
- Dockerfile supply-chain safeguards

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
- `make start`
- `make pulumi-preview`
- `make pulumi-up`
- `make pulumi-refresh`
- `make pulumi-destroy`
- `make sh`

## Full local run

Run the standard local validation battery with:

```bash
make test
make test-mutation
```

Use `make pulumi-preview` before any real cloud deployment.
