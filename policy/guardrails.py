"""Reusable validators for the infrastructure-template Pulumi policy pack."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

REQUIRED_TAGS = ("Project", "Environment")
PUBLIC_S3_ACLS = {"public-read", "public-read-write"}
OPEN_CIDRS = ("0.0.0.0/0", "::/0")
SENSITIVE_PORTS = (22, 3389)
S3_BUCKET_TYPE_SUFFIX = "s3/bucket:Bucket"
SECURITY_GROUP_RULE_TYPE_SUFFIX = "ec2/securityGroupRule:SecurityGroupRule"
SECURITY_GROUP_TYPE_SUFFIX = "ec2/securityGroup:SecurityGroup"


def extract_tags(props: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Return the resource tag mapping when the provider exposes one."""
    tags = props.get("tags")
    if isinstance(tags, Mapping):
        return tags

    tags_all = props.get("tagsAll")
    if isinstance(tags_all, Mapping):
        return tags_all

    return None


def missing_required_tags(tags: Mapping[str, Any] | None) -> list[str]:
    """Return required default tags that are absent or blank."""
    if tags is None:
        return []

    missing = []
    for key in REQUIRED_TAGS:
        value = tags.get(key)
        if not isinstance(value, str) or not value.strip():
            missing.append(key)
    return missing


def has_public_s3_acl(resource_type: str, props: Mapping[str, Any]) -> bool:
    """Detect explicitly public S3 bucket ACLs."""
    return _matches_resource_type(resource_type, S3_BUCKET_TYPE_SUFFIX) and (
        props.get("acl") in PUBLIC_S3_ACLS
    )


def open_admin_ports(resource_type: str, props: Mapping[str, Any]) -> list[int]:
    """Return sensitive ports exposed to the public internet."""
    exposed_ports: set[int] = set()

    if _matches_resource_type(resource_type, SECURITY_GROUP_RULE_TYPE_SUFFIX):
        if props.get("type") == "ingress" and _is_open_to_world(props):
            exposed_ports.update(_ports_in_range(props))

    if _matches_resource_type(resource_type, SECURITY_GROUP_TYPE_SUFFIX):
        for rule in props.get("ingress", []) or []:
            if isinstance(rule, Mapping) and _is_open_to_world(rule):
                exposed_ports.update(_ports_in_range(rule))

    return sorted(exposed_ports)


def _is_open_to_world(props: Mapping[str, Any]) -> bool:
    """Return whether a rule exposes traffic to all IPv4 or IPv6 addresses."""
    return _contains_open_cidr(props.get("cidrBlocks")) or _contains_open_cidr(
        props.get("ipv6CidrBlocks")
    )


def _matches_resource_type(resource_type: str, suffix: str) -> bool:
    """Allow equivalent package prefixes while keeping the module/type contract."""
    return resource_type.endswith(suffix)


def _contains_open_cidr(value: Any) -> bool:
    """Handle both provider scalar and list representations for CIDR blocks."""
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(cidr in OPEN_CIDRS for cidr in value)

    return value in OPEN_CIDRS


def _ports_in_range(props: Mapping[str, Any]) -> set[int]:
    """Return tracked sensitive ports within the rule's from/to range."""
    from_port = props.get("fromPort")
    to_port = props.get("toPort")

    if not isinstance(from_port, int) or not isinstance(to_port, int):
        return set()

    return {port for port in SENSITIVE_PORTS if from_port <= port and port <= to_port}
