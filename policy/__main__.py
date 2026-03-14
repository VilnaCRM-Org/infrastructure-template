"""Pulumi policy pack entrypoint."""

from pulumi_policy import PolicyPack

try:
    from policy.pack import POLICY_PACK_NAME, build_policies
except ModuleNotFoundError:  # pragma: no cover - exercised by Pulumi CLI startup.
    from pack import POLICY_PACK_NAME, build_policies

PolicyPack(
    name=POLICY_PACK_NAME,
    policies=build_policies(),
)
