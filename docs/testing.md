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
- `policy/PulumiPolicy.yaml`
- Release workflow contracts
- Dockerfile supply-chain safeguards

## Policy tests

Run with:

```bash
make test-policy
```

Coverage:

- `policy/guardrails.py`
- `policy/pack.py`
- Pulumi policy pack registration in `policy/__main__.py`
- Required tag, public S3 ACL, and open admin-port guardrails
- 100% line coverage for the policy-pack Python surface

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
- `pulumi/app/guardrails.py`
- Config fallback behavior for `environment` and `serviceName`
- Identifier validation and fail-fast guardrails
- Component type token and exported outputs
- 100% line coverage for the Pulumi application layer

## Integration tests

Run with:

```bash
make test-integration
```

Coverage:

- The real `pulumi/__main__.py` entrypoint
- Pulumi Automation lifecycle behavior with a local backend
- Real Pulumi policy-pack startup and enforcement through `pulumi preview --policy-pack`
- Guardrail resolution contracts for explicit, configured, and default metadata
- Output wiring for environment metadata
- 100% line coverage enforced for the integration-covered Pulumi program files

The Docker workspace keeps its `uv` virtual environment outside the bind-mounted
repository tree so Pulumi always sees a stable interpreter with `pip`
available for plugin discovery. The policy-pack bootstrap reuses that same
environment and resyncs it from `uv.lock` when Python dependencies drift.

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

Run `make test` during normal iteration when you want the fast structural, policy, quality, unit, integration, and CLI suites after a prerequisite sanity check. For the same non-mutation battery that GitHub runs in `pulumi-local.yml`, run `make ci-pr`. Before pushing, execute `make ci` to run the full local equivalent of every GitHub check, including the prerequisite check, Docker build, and mutation suite.

GitHub Actions now mirrors `make ci-pr` through the `Pulumi Local Test Battery` workflow, while `Pulumi Mutation Tests` keeps mutation analysis isolated as a separate check.
The `Pulumi Policy Tests` workflow runs the policy-pack coverage suite, and the `Python Quality Checks` workflow runs Ruff and Ty as dedicated quality gates.

Use `make pulumi-preview` before any real cloud deployment. The preview and
apply targets automatically enable the repository policy pack.
