# SRE Operations Guide

This guide covers the day-2 operating model for the template: validating local
prerequisites, previewing changes safely, and handling common infrastructure
maintenance flows.

## Preflight

Run the basic workstation check before blaming Docker, Pulumi, or CI:

```bash
make doctor
```

The command verifies that Docker and Docker Compose are available, reports the
effective env file, and prints the service and Pulumi directory that the
Makefile will target. It does not print secrets.

## Daily Workflow

For the normal edit-test loop:

```bash
make test
```

Before pushing a branch that changes infrastructure logic, Docker wiring, or CI
contracts, use the same non-mutation battery that GitHub runs in
`pulumi-local.yml`:

```bash
make ci-pr
```

When you also want the dedicated mutation suite locally:

```bash
make ci
```

Use `make ci-pr` to catch the same structural, quality, unit, integration, and
CLI regressions that GitHub runs before merge. Use `make ci` when you also want
the mutation suite before the branch reaches GitHub Actions.

## Preview and Apply

Use previews as the default gate for real infrastructure changes:

```bash
make pulumi-preview
```

Apply only after the preview is understood and reviewed:

```bash
make pulumi-up
pulumi -C pulumi stack output
```

For drift reconciliation without applying a fresh plan:

```bash
make pulumi-refresh
```

For teardown:

```bash
make pulumi-destroy
```

Treat destroy as irreversible unless you have a tested restore path.

## Stack Strategy

Recommended stack patterns:

- `dev` for shared baseline development
- `pr-<number>` for short-lived validation environments
- `smoke` for manual release verification

Avoid mixing unrelated validation work into one long-lived shared stack. It
makes previews noisy and rollback decisions ambiguous.

## Incident and Drift Triage

When something looks wrong:

1. run `make doctor`
2. run `make test` to separate local code issues from cloud drift
3. run `make pulumi-refresh` if the concern is live-state drift
4. inspect `pulumi -C pulumi stack output` for the non-secret state you expect
5. use an ephemeral stack for risky experiments instead of debugging directly in
   a shared environment

## CI Troubleshooting

Map failures back to their local commands:

- `Structural` -> `make test-pulumi`
- `Ruff` -> `make test-ruff`
- `Ty` -> `make test-ty`
- `Unit` -> `make test-unit`
- `Integration` -> `make test-integration`
- `Mutation` -> `make test-mutation`
- `Run Bats Tests` -> `make test-cli`
- `Local Battery` -> `make ci-pr`

That mapping is intentional. If a failure cannot be reproduced locally with the
matching target, the problem is probably workflow-specific and should be treated
as a CI contract issue.

## Release Hygiene

Release automation should stay boring:

- keep changelog generation deterministic
- use the documented token fallback contract
- avoid mixing release logic with deployment logic
- prefer one-purpose workflows over single giant pipelines

## Cleanup

When local state gets messy:

```bash
make clean
```

This removes Compose state and Python build artifacts without touching cloud
resources.
