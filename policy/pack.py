"""Pulumi policy definitions for the infrastructure template."""

from __future__ import annotations

try:
    from policy.guardrails import (
        extract_tags,
        has_public_s3_acl,
        missing_required_tags,
        open_admin_ports,
    )
except ModuleNotFoundError:  # pragma: no cover - exercised by direct script startup.
    from guardrails import (
        extract_tags,
        has_public_s3_acl,
        missing_required_tags,
        open_admin_ports,
    )
from pulumi_policy import (
    EnforcementLevel,
    ReportViolation,
    ResourceValidationArgs,
    ResourceValidationPolicy,
)

POLICY_PACK_NAME = "infrastructure-template-guardrails"


def require_default_tags(
    args: ResourceValidationArgs, report_violation: ReportViolation
) -> None:
    """Require default project and environment tags on tagged AWS resources."""
    if not args.resource_type.startswith("aws:"):
        return

    if "tags" not in args.props and "tagsAll" not in args.props:
        return

    missing = missing_required_tags(extract_tags(args.props))
    if missing:
        report_violation(
            "AWS resources with tags must include non-empty default tags: "
            + ", ".join(missing)
            + "."
        )


def block_public_s3_acls(
    args: ResourceValidationArgs, report_violation: ReportViolation
) -> None:
    """Prevent public ACLs on S3 buckets."""
    if has_public_s3_acl(args.resource_type, args.props):
        report_violation(
            "S3 buckets must not use public-read or public-read-write ACLs."
        )


def block_open_admin_ports(
    args: ResourceValidationArgs, report_violation: ReportViolation
) -> None:
    """Prevent public exposure of SSH and RDP through security groups."""
    ports = open_admin_ports(args.resource_type, args.props)
    if ports:
        report_violation(
            "Security groups must not expose admin ports to the public internet: "
            + ", ".join(str(port) for port in ports)
            + "."
        )


def build_policies() -> list[ResourceValidationPolicy]:
    """Construct the policy list exported by the Pulumi policy pack."""
    return [
        ResourceValidationPolicy(
            name="aws-resource-required-default-tags",
            description="Require Project and Environment tags on tagged AWS resources.",
            enforcement_level=EnforcementLevel.MANDATORY,
            validate=require_default_tags,
        ),
        ResourceValidationPolicy(
            name="s3-no-public-acls",
            description="Disallow public ACLs on AWS S3 buckets.",
            enforcement_level=EnforcementLevel.MANDATORY,
            validate=block_public_s3_acls,
        ),
        ResourceValidationPolicy(
            name="security-group-no-open-admin-ports",
            description="Disallow public SSH and RDP exposure in security groups.",
            enforcement_level=EnforcementLevel.MANDATORY,
            validate=block_open_admin_ports,
        ),
    ]
