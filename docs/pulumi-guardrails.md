# Pulumi Guardrails

This repository enforces guardrails in two layers so invalid infrastructure
changes fail early and consistently.

## Runtime guardrails

The Pulumi application layer validates stack metadata before it becomes a
Pulumi `Output`.

- `environment` must be a lowercase slug made of letters, digits, and hyphens.
- `serviceName` must follow the same rule.
- Empty values and surrounding whitespace are rejected.

Those checks live in `pulumi/app/guardrails.py` and are applied by
`EnvironmentSettings` before stack exports and default tags are derived.

## Policy pack

The `policy/` directory contains a Python Pulumi policy pack for AWS resources.
It currently enforces three mandatory rules:

- tagged AWS resources must include non-empty `Project` and `Environment` tags
- S3 buckets and dedicated bucket ACL resources must not use `public-read` or `public-read-write` ACLs
- security groups must not expose SSH or RDP to `0.0.0.0/0` or `::/0`, including modern ingress-rule resources that use `cidrIpv4` or `cidrIpv6`

The policy-pack source is split so the reusable validation logic is easy to
test:

- `policy/guardrails.py` contains pure validation helpers
- `policy/pack.py` defines the Pulumi policy validators and policy list
- `policy/__main__.py` registers the `PolicyPack`
- `policy/PulumiPolicy.yaml` defines the runtime contract for Pulumi
- `scripts/prepare_policy_pack.sh` keeps the shared `uv` environment ready for
  Pulumi's Python policy runtime

## Local validation

Use the focused suite when you are editing guardrail logic:

```bash
make test-policy
```

That command enforces 100% line coverage for the Python policy-pack code.
`make test-unit` and `make test-integration` keep the Pulumi application layer
under the same 100% line-coverage contract, so both runtime guardrails and
policy guardrails fail fast when tests drift.

`make pulumi-preview` and `make pulumi-up` also enable the policy pack by
default. Before Pulumi starts, the repository checks that the shared
container-managed `uv` environment contains both `pulumi` and
`pulumi-policy`; if the branch changed Python dependencies, the helper resyncs
the environment from `uv.lock`.

For the full non-mutation PR battery:

```bash
make ci-pr
```

For the full local superset, including mutation:

```bash
make ci
```

## CI mapping

GitHub Actions runs `make test-policy` in `pulumi-policy.yml` and also exercises
the policy suite through `make ci-pr` in the local-battery workflow. This keeps
the focused policy check and the aggregate PR battery aligned.

The integration suite also runs a real `pulumi preview --policy-pack ...`
against a local backend, so policy startup failures and public-ACL violations
are caught before merge.
