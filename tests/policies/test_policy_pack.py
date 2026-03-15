"""Tests for the Pulumi policy pack and reusable guardrail helpers."""

from __future__ import annotations

import importlib.util
import runpy
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pulumi_policy
import pytest
from pulumi_policy import EnforcementLevel

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POLICY_DIR = PROJECT_ROOT / "policy"
POLICY_MAIN = POLICY_DIR / "__main__.py"


@pytest.fixture
def policy_runtime(monkeypatch: pytest.MonkeyPatch) -> SimpleNamespace:
    """Import the policy modules through the package path without leaking globals."""
    for module_name in ("guardrails", "pack", "policy.guardrails", "policy.pack"):
        monkeypatch.delitem(sys.modules, module_name, raising=False)

    injected_modules: set[str] = set()

    def load_module(module_name: str, path: Path):
        """Load a policy module from disk without leaving global imports behind."""
        spec = importlib.util.spec_from_file_location(module_name, path)
        assert spec is not None
        assert spec.loader is not None

        module = importlib.util.module_from_spec(spec)
        injected_modules.add(module_name)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
        except Exception:
            injected_modules.discard(module_name)
            sys.modules.pop(module_name, None)
            raise
        return module

    guardrails = load_module("guardrails", POLICY_DIR / "guardrails.py")
    pack = load_module("pack", POLICY_DIR / "pack.py")

    try:
        yield SimpleNamespace(
            extract_tags=guardrails.extract_tags,
            has_public_s3_acl=guardrails.has_public_s3_acl,
            missing_required_tags=guardrails.missing_required_tags,
            open_admin_ports=guardrails.open_admin_ports,
            POLICY_PACK_NAME=pack.POLICY_PACK_NAME,
            block_open_admin_ports=pack.block_open_admin_ports,
            block_public_s3_acls=pack.block_public_s3_acls,
            build_policies=pack.build_policies,
            require_default_tags=pack.require_default_tags,
        )
    finally:
        for module_name in injected_modules:
            sys.modules.pop(module_name, None)


def _policy_args(resource_type: str, props: dict[str, Any]) -> SimpleNamespace:
    """Create the subset of Pulumi policy args needed by the validators."""
    return SimpleNamespace(resource_type=resource_type, props=props)


def _collect_violations(
    validator, *, resource_type: str, props: dict[str, Any]
) -> list[str]:
    """Run a validator and capture every reported violation."""
    violations: list[str] = []
    validator(_policy_args(resource_type, props), violations.append)
    return violations


def test_extract_tags_prefers_tags_and_falls_back_to_tags_all(
    policy_runtime: SimpleNamespace,
) -> None:
    """Support both provider tag shapes without guessing."""
    assert policy_runtime.extract_tags({"tags": {"Project": "svc"}}) == {
        "Project": "svc"
    }
    assert policy_runtime.extract_tags(
        {"tags": "invalid", "tagsAll": {"Environment": "dev"}}
    ) == {"Environment": "dev"}
    assert policy_runtime.extract_tags({}) is None


def test_missing_required_tags_reports_blank_or_missing_values(
    policy_runtime: SimpleNamespace,
) -> None:
    """Detect blank or absent required default tags."""
    assert policy_runtime.missing_required_tags(None) == []
    assert (
        policy_runtime.missing_required_tags({"Project": "svc", "Environment": "dev"})
        == []
    )
    assert policy_runtime.missing_required_tags(
        {"Project": " ", "Environment": "dev"}
    ) == ["Project"]
    assert policy_runtime.missing_required_tags({"Project": "svc"}) == ["Environment"]


def test_has_public_s3_acl_detects_public_acls_only(
    policy_runtime: SimpleNamespace,
) -> None:
    """Only public S3 ACLs should trigger the guardrail."""
    assert (
        policy_runtime.has_public_s3_acl(
            "aws:s3/bucket:Bucket", {"acl": "public-read-write"}
        )
        is True
    )
    assert (
        policy_runtime.has_public_s3_acl(
            "tests:s3/bucket:Bucket", {"acl": "public-read"}
        )
        is True
    )
    assert (
        policy_runtime.has_public_s3_acl(
            "aws:s3/bucketAcl:BucketAcl", {"acl": "public-read"}
        )
        is True
    )
    assert (
        policy_runtime.has_public_s3_acl(
            "aws:s3/bucketAclV2:BucketAclV2", {"acl": "public-read-write"}
        )
        is True
    )
    assert (
        policy_runtime.has_public_s3_acl("aws:s3/bucket:Bucket", {"acl": "private"})
        is False
    )
    assert (
        policy_runtime.has_public_s3_acl("aws:s3/object:Object", {"acl": "public-read"})
        is False
    )


def test_open_admin_ports_detects_public_security_group_rules(
    policy_runtime: SimpleNamespace,
) -> None:
    """Catch admin ports exposed through standalone security-group rules."""
    assert policy_runtime.open_admin_ports(
        "aws:ec2/securityGroupRule:SecurityGroupRule",
        {
            "type": "ingress",
            "fromPort": 22,
            "toPort": 22,
            "cidrBlocks": ["0.0.0.0/0"],
        },
    ) == [22]
    assert policy_runtime.open_admin_ports(
        "tests:ec2/securityGroupRule:SecurityGroupRule",
        {
            "type": "ingress",
            "fromPort": 3389,
            "toPort": 3389,
            "cidrBlocks": ["0.0.0.0/0"],
        },
    ) == [3389]


def test_open_admin_ports_detects_public_inline_security_group_rules(
    policy_runtime: SimpleNamespace,
) -> None:
    """Catch inline ingress rules that expose RDP publicly."""
    assert policy_runtime.open_admin_ports(
        "aws:ec2/securityGroup:SecurityGroup",
        {
            "ingress": [
                {
                    "fromPort": 3389,
                    "toPort": 3389,
                    "ipv6CidrBlocks": "::/0",
                }
            ]
        },
    ) == [3389]


def test_open_admin_ports_detects_modern_ingress_rules_and_all_protocols(
    policy_runtime: SimpleNamespace,
) -> None:
    """Catch VPC ingress-rule resources that expose sensitive ports publicly."""
    assert policy_runtime.open_admin_ports(
        "aws:vpc/securityGroupIngressRule:SecurityGroupIngressRule",
        {
            "cidrIpv4": "0.0.0.0/0",
            "ipProtocol": "-1",
        },
    ) == [22, 3389]
    assert policy_runtime.open_admin_ports(
        "aws:vpc/securityGroupIngressRule:SecurityGroupIngressRule",
        {
            "cidrIpv6": "::/0",
            "ipProtocol": "all",
        },
    ) == [22, 3389]
    assert policy_runtime.open_admin_ports(
        "aws:ec2/securityGroupRule:SecurityGroupRule",
        {
            "type": "ingress",
            "cidrBlocks": ["0.0.0.0/0"],
            "protocol": "-1",
        },
    ) == [22, 3389]


def test_open_admin_ports_ignores_safe_or_malformed_rules(
    policy_runtime: SimpleNamespace,
) -> None:
    """Ignore private or malformed rule shapes instead of crashing."""
    assert (
        policy_runtime.open_admin_ports(
            "aws:ec2/securityGroupRule:SecurityGroupRule",
            {
                "type": "egress",
                "fromPort": 22,
                "toPort": 22,
                "cidrBlocks": ["0.0.0.0/0"],
            },
        )
        == []
    )
    assert (
        policy_runtime.open_admin_ports(
            "aws:ec2/securityGroupRule:SecurityGroupRule",
            {
                "type": "ingress",
                "fromPort": "22",
                "toPort": 22,
                "cidrBlocks": ["0.0.0.0/0"],
            },
        )
        == []
    )
    assert (
        policy_runtime.open_admin_ports("aws:s3/bucket:Bucket", {"acl": "private"})
        == []
    )


def test_require_default_tags_validator_reports_missing_tags(
    policy_runtime: SimpleNamespace,
) -> None:
    """Require the template's default tags on tagged AWS resources."""
    assert (
        _collect_violations(
            policy_runtime.require_default_tags,
            resource_type="kubernetes:core/v1:Namespace",
            props={"metadata": {"name": "dev"}},
        )
        == []
    )
    assert (
        _collect_violations(
            policy_runtime.require_default_tags,
            resource_type="aws:s3/bucket:Bucket",
            props={},
        )
        == []
    )
    assert (
        _collect_violations(
            policy_runtime.require_default_tags,
            resource_type="aws:s3/bucket:Bucket",
            props={"tags": {"Project": "svc", "Environment": "dev"}},
        )
        == []
    )

    violations = _collect_violations(
        policy_runtime.require_default_tags,
        resource_type="aws:ec2/instance:Instance",
        props={"tags": {"Project": "svc"}},
    )

    assert violations == [
        "AWS resources with tags must include non-empty default tags: Environment."
    ]


def test_block_public_s3_acls_validator_reports_public_buckets(
    policy_runtime: SimpleNamespace,
) -> None:
    """Reject public ACLs while leaving other resources alone."""
    assert (
        _collect_violations(
            policy_runtime.block_public_s3_acls,
            resource_type="aws:s3/bucket:Bucket",
            props={"acl": "private"},
        )
        == []
    )

    violations = _collect_violations(
        policy_runtime.block_public_s3_acls,
        resource_type="aws:s3/bucket:Bucket",
        props={"acl": "public-read"},
    )

    assert violations == [
        "S3 buckets must not use public-read or public-read-write ACLs."
    ]

    dedicated_acl_violations = _collect_violations(
        policy_runtime.block_public_s3_acls,
        resource_type="aws:s3/bucketAcl:BucketAcl",
        props={"acl": "public-read"},
    )

    assert dedicated_acl_violations == [
        "S3 buckets must not use public-read or public-read-write ACLs."
    ]


def test_block_open_admin_ports_validator_reports_public_admin_access(
    policy_runtime: SimpleNamespace,
) -> None:
    """Reject world-open SSH and RDP rules."""
    assert (
        _collect_violations(
            policy_runtime.block_open_admin_ports,
            resource_type="aws:ec2/securityGroup:SecurityGroup",
            props={
                "ingress": [
                    {
                        "fromPort": 443,
                        "toPort": 443,
                        "cidrBlocks": ["0.0.0.0/0"],
                    }
                ]
            },
        )
        == []
    )

    violations = _collect_violations(
        policy_runtime.block_open_admin_ports,
        resource_type="aws:ec2/securityGroupRule:SecurityGroupRule",
        props={
            "type": "ingress",
            "fromPort": 22,
            "toPort": 22,
            "cidrBlocks": ["0.0.0.0/0"],
        },
    )

    assert violations == [
        "Security groups must not expose admin ports to the public internet: 22."
    ]

    modern_rule_violations = _collect_violations(
        policy_runtime.block_open_admin_ports,
        resource_type="aws:vpc/securityGroupIngressRule:SecurityGroupIngressRule",
        props={
            "cidrIpv4": "0.0.0.0/0",
            "ipProtocol": "-1",
        },
    )

    assert modern_rule_violations == [
        "Security groups must not expose admin ports to the public internet: 22, 3389."
    ]


def test_build_policies_returns_mandatory_guardrails(
    policy_runtime: SimpleNamespace,
) -> None:
    """Expose the expected mandatory guardrails in the policy pack."""
    policies = policy_runtime.build_policies()

    assert [policy.name for policy in policies] == [
        "aws-resource-required-default-tags",
        "s3-no-public-acls",
        "security-group-no-open-admin-ports",
    ]
    assert all(
        policy.enforcement_level == EnforcementLevel.MANDATORY for policy in policies
    )


def test_policy_entrypoint_registers_expected_policy_pack(
    monkeypatch: pytest.MonkeyPatch, policy_runtime: SimpleNamespace
) -> None:
    """Wire the guardrail list into a PolicyPack at import time."""
    captured: dict[str, Any] = {}

    def fake_policy_pack(*, name: str, policies: list[Any]) -> dict[str, Any]:
        captured["name"] = name
        captured["policies"] = policies
        return captured

    monkeypatch.setattr(pulumi_policy, "PolicyPack", fake_policy_pack)

    runpy.run_path(str(POLICY_MAIN), run_name="__main__")

    assert captured["name"] == policy_runtime.POLICY_PACK_NAME
    assert [policy.name for policy in captured["policies"]] == [
        "aws-resource-required-default-tags",
        "s3-no-public-acls",
        "security-group-no-open-admin-ports",
    ]
