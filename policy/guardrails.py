"""Reusable validators for the VilnaCRM Pulumi policy pack."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any, cast

try:
    from policy.config import PolicyConfig, load_policy_config
except ModuleNotFoundError:  # pragma: no cover - exercised by direct policy startup.
    from config import PolicyConfig, load_policy_config

CONFIG = load_policy_config()
PUBLIC_S3_ACLS = {"public-read", "public-read-write"}
OPEN_CIDRS = ("0.0.0.0/0", "::/0")
SENSITIVE_PORTS = (22, 3389)
AWS_PROVIDER_TYPE_SUFFIX = "providers:Provider"
S3_BUCKET_TYPE_SUFFIX = "s3/bucket:Bucket"
S3_BUCKET_ACL_TYPE_SUFFIX = "s3/bucketAcl:BucketAcl"
S3_BUCKET_ACL_V2_TYPE_SUFFIX = "s3/bucketAclV2:BucketAclV2"
S3_BUCKET_POLICY_TYPE_SUFFIX = "s3/bucketPolicy:BucketPolicy"
EBS_VOLUME_TYPE_SUFFIX = "ec2/volume:Volume"
EFS_FILE_SYSTEM_TYPE_SUFFIX = "efs/fileSystem:FileSystem"
RDS_CLUSTER_TYPE_SUFFIX = "rds/cluster:Cluster"
RDS_INSTANCE_TYPE_SUFFIX = "rds/instance:Instance"
LOAD_BALANCER_TYPE_SUFFIX = "lb/loadBalancer:LoadBalancer"
SECURITY_GROUP_RULE_TYPE_SUFFIX = "ec2/securityGroupRule:SecurityGroupRule"
SECURITY_GROUP_TYPE_SUFFIX = "ec2/securityGroup:SecurityGroup"
SECURITY_GROUP_INGRESS_RULE_TYPE_SUFFIX = (
    "vpc/securityGroupIngressRule:SecurityGroupIngressRule"
)
IDENTITY_POLICY_TYPE_SUFFIXES = (
    "iam/policy:Policy",
    "iam/rolePolicy:RolePolicy",
    "iam/groupPolicy:GroupPolicy",
    "iam/userPolicy:UserPolicy",
)


def extract_tags(props: Mapping[str, Any]) -> Mapping[str, Any] | None:
    """Return the resource tag mapping when the provider exposes one."""
    tags = props.get("tags")
    if isinstance(tags, Mapping):
        return tags

    tags_all = props.get("tagsAll")
    if isinstance(tags_all, Mapping):
        return tags_all

    return None


def missing_required_tags(
    tags: Mapping[str, Any] | None, config: PolicyConfig = CONFIG
) -> list[str]:
    """Return required default tags that are absent or blank."""
    if tags is None:
        return []

    missing = []
    for key in config.required_tags:
        value = tags.get(key)
        if not isinstance(value, str) or not value.strip():
            missing.append(key)
    return missing


def has_public_s3_acl(resource_type: str, props: Mapping[str, Any]) -> bool:
    """Detect explicitly public S3 bucket ACLs."""
    return _matches_any_resource_type(
        resource_type,
        (
            S3_BUCKET_TYPE_SUFFIX,
            S3_BUCKET_ACL_TYPE_SUFFIX,
            S3_BUCKET_ACL_V2_TYPE_SUFFIX,
        ),
    ) and (props.get("acl") in PUBLIC_S3_ACLS)


def has_public_s3_bucket_policy(resource_type: str, props: Mapping[str, Any]) -> bool:
    """Detect bucket policies that allow public access."""
    if not _matches_resource_type(resource_type, S3_BUCKET_POLICY_TYPE_SUFFIX):
        return False

    for statement in _policy_statements(props):
        if _statement_allows_public_access(statement):
            return True
    return False


def is_public_bucket_allowlisted(
    props: Mapping[str, Any], config: PolicyConfig = CONFIG
) -> bool:
    """Allow explicit public buckets only through an allowlist or tag annotation."""
    bucket_name = _string_value(props.get("bucket"))
    if bucket_name and bucket_name in config.public_s3_bucket_allowlist:
        return True

    tags = extract_tags(props) or {}
    tag_name = config.annotations.get("public_s3_tag", "AllowPublicBucket")
    return _truthy(tags.get(tag_name))


def invalid_region(
    resource_type: str, props: Mapping[str, Any], config: PolicyConfig = CONFIG
) -> str | None:
    """Reject regions outside the repository allowlist when explicitly configured."""
    if not config.allowed_regions:
        return None

    if not (
        resource_type.startswith("aws:")
        or _matches_resource_type(resource_type, AWS_PROVIDER_TYPE_SUFFIX)
    ):
        return None

    region = _string_value(props.get("region"))
    if region is None or region in config.allowed_regions:
        return None
    return region


def storage_encryption_violations(
    resource_type: str, props: Mapping[str, Any]
) -> list[str]:
    """Return storage encryption issues for critical persistent resources."""
    violations: list[str] = []

    if _matches_resource_type(resource_type, S3_BUCKET_TYPE_SUFFIX):
        encryption = props.get("serverSideEncryptionConfiguration")
        if not isinstance(encryption, Mapping):
            violations.append("S3 buckets must enable default server-side encryption.")

    if _matches_resource_type(resource_type, EBS_VOLUME_TYPE_SUFFIX) and not _truthy(
        props.get("encrypted")
    ):
        violations.append("EBS volumes must enable encryption at rest.")

    if _matches_resource_type(
        resource_type, EFS_FILE_SYSTEM_TYPE_SUFFIX
    ) and not _truthy(props.get("encrypted")):
        violations.append("EFS file systems must enable encryption at rest.")

    if _matches_any_resource_type(
        resource_type, (RDS_CLUSTER_TYPE_SUFFIX, RDS_INSTANCE_TYPE_SUFFIX)
    ) and not _truthy(props.get("storageEncrypted")):
        violations.append("RDS databases must enable storage encryption.")

    return violations


def logging_violations(resource_type: str, props: Mapping[str, Any]) -> list[str]:
    """Return logging configuration issues for supported resource types."""
    violations: list[str] = []

    if _matches_resource_type(resource_type, S3_BUCKET_TYPE_SUFFIX):
        logging_config = props.get("logging")
        if not isinstance(logging_config, Mapping) or not _string_value(
            logging_config.get("targetBucket")
        ):
            violations.append("S3 buckets must send access logs to a target bucket.")

    if _matches_resource_type(resource_type, LOAD_BALANCER_TYPE_SUFFIX):
        access_logs = props.get("accessLogs")
        if not isinstance(access_logs, Mapping) or not _truthy(
            access_logs.get("enabled")
        ):
            violations.append("Load balancers must enable access logs.")

    return violations


def wildcard_iam_violations(
    resource_type: str,
    props: Mapping[str, Any],
    config: PolicyConfig = CONFIG,
) -> list[str]:
    """Reject wildcard IAM permissions unless explicitly allowlisted."""
    identifier = iam_policy_identifier(props)
    if identifier and identifier in config.wildcard_iam_allowlist:
        return []

    tags = extract_tags(props) or {}
    allow_tag = config.annotations.get("wildcard_iam_tag", "AllowWildcardIam")
    reason_tag = config.annotations.get(
        "wildcard_iam_reason_tag", "AllowWildcardIamReason"
    )
    if _truthy(tags.get(allow_tag)) and _string_value(tags.get(reason_tag)):
        return []

    documents = list(_policy_documents(resource_type, props))
    violations: list[str] = []
    for field_name, statements in documents:
        for statement in statements:
            if _statement_contains_wildcard_permissions(statement):
                violations.append(
                    f"{field_name} must not use wildcard IAM permissions "
                    "without an explicit allowlist."
                )
                break
    return violations


def iam_policy_identifier(props: Mapping[str, Any]) -> str | None:
    """Return a stable identifier for policy allowlists when one is available."""
    for key in ("name", "policyName", "bucket", "role", "group", "user"):
        value = _string_value(props.get(key))
        if value:
            return value
    return None


def production_database_violations(
    resource_type: str,
    props: Mapping[str, Any],
    config: PolicyConfig = CONFIG,
) -> list[str]:
    """Enforce safer database defaults for production-like environments."""
    if not _matches_any_resource_type(
        resource_type, (RDS_CLUSTER_TYPE_SUFFIX, RDS_INSTANCE_TYPE_SUFFIX)
    ):
        return []

    environment = _string_value((extract_tags(props) or {}).get("Environment"))
    if environment is None or environment.lower() not in config.production_environments:
        return []

    violations: list[str] = []
    if not _truthy(props.get("deletionProtection")):
        violations.append("Production databases must enable deletion protection.")
    if _truthy(props.get("skipFinalSnapshot")):
        violations.append("Production databases must keep final snapshots enabled.")
    if _truthy(props.get("publiclyAccessible")):
        violations.append("Production databases must not be publicly accessible.")
    return violations


def open_admin_ports(resource_type: str, props: Mapping[str, Any]) -> list[int]:
    """Return sensitive ports exposed to the public internet."""
    exposed_ports: set[int] = set()

    if _matches_resource_type(resource_type, SECURITY_GROUP_RULE_TYPE_SUFFIX):
        if props.get("type") == "ingress" and _is_open_to_world(props):
            exposed_ports.update(_ports_in_range(props))

    if _matches_resource_type(resource_type, SECURITY_GROUP_INGRESS_RULE_TYPE_SUFFIX):
        if _is_open_to_world(props):
            exposed_ports.update(_ports_in_range(props))

    if _matches_resource_type(resource_type, SECURITY_GROUP_TYPE_SUFFIX):
        for rule in props.get("ingress", []) or []:
            if isinstance(rule, Mapping) and _is_open_to_world(rule):
                exposed_ports.update(_ports_in_range(rule))

    return sorted(exposed_ports)


def _policy_documents(
    resource_type: str, props: Mapping[str, Any]
) -> Sequence[tuple[str, Sequence[Mapping[str, Any]]]]:
    """Return every IAM policy document embedded in a resource."""
    documents: list[tuple[str, Sequence[Mapping[str, Any]]]] = []

    for field_name in ("policy", "policyDocument", "assumeRolePolicy"):
        statements = _policy_statements_from_value(props.get(field_name))
        if statements:
            documents.append((field_name, statements))

    if _matches_any_resource_type(resource_type, IDENTITY_POLICY_TYPE_SUFFIXES):
        return documents

    inline_policies = props.get("inlinePolicies")
    if isinstance(inline_policies, Sequence) and not isinstance(
        inline_policies, (str, bytes)
    ):
        for index, policy in enumerate(inline_policies):
            if not isinstance(policy, Mapping):
                continue
            statements = _policy_statements_from_value(policy.get("policy"))
            if statements:
                documents.append((f"inlinePolicies[{index}].policy", statements))
    return documents


def _policy_statements(props: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    """Extract policy statements from common Pulumi resource property shapes."""
    for field_name in ("policy", "policyDocument"):
        statements = _policy_statements_from_value(props.get(field_name))
        if statements:
            return statements
    return []


def _policy_statements_from_value(value: object) -> Sequence[Mapping[str, Any]]:
    """Parse a policy document string or mapping and return statement objects."""
    document = _parse_json_document(value)
    if not isinstance(document, Mapping):
        return []

    statements = document.get("Statement")
    if isinstance(statements, Mapping):
        return [statements]
    if isinstance(statements, Sequence) and not isinstance(statements, (str, bytes)):
        return [statement for statement in statements if isinstance(statement, Mapping)]
    return []


def _parse_json_document(value: object) -> Mapping[str, Any] | None:
    """Parse a JSON document if one is present and valid."""
    if isinstance(value, Mapping):
        return cast(Mapping[str, Any], value)
    if not isinstance(value, str):
        return None
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, Mapping) else None


def _statement_allows_public_access(statement: Mapping[str, Any]) -> bool:
    """Detect allow statements that grant public access to everyone."""
    effect = _string_value(statement.get("Effect"))
    if effect != "Allow":
        return False

    principal = statement.get("Principal")
    if principal == "*":
        return True

    if isinstance(principal, Mapping):
        for value in principal.values():
            if value == "*":
                return True
            if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
                if "*" in value:
                    return True
    return False


def _statement_contains_wildcard_permissions(statement: Mapping[str, Any]) -> bool:
    """Reject Action=* or Resource=* patterns inside IAM policies."""
    effect = _string_value(statement.get("Effect"))
    if effect != "Allow":
        return False

    return _contains_wildcard(statement.get("Action")) or _contains_wildcard(
        statement.get("Resource")
    )


def _contains_wildcard(value: object) -> bool:
    """Handle both scalar and list forms of wildcard policy values."""
    if value == "*":
        return True
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(item == "*" for item in value)
    return False


def _is_open_to_world(props: Mapping[str, Any]) -> bool:
    """Return whether a rule exposes traffic to all IPv4 or IPv6 addresses."""
    return any(
        _contains_open_cidr(props.get(key))
        for key in ("cidrBlocks", "ipv6CidrBlocks", "cidrIpv4", "cidrIpv6")
    )


def _matches_resource_type(resource_type: str, suffix: str) -> bool:
    """Allow equivalent package prefixes while keeping the module/type contract."""
    return resource_type.endswith(suffix)


def _matches_any_resource_type(resource_type: str, suffixes: Sequence[str]) -> bool:
    """Check multiple equivalent provider suffixes without hardcoding package names."""
    return any(_matches_resource_type(resource_type, suffix) for suffix in suffixes)


def _contains_open_cidr(value: Any) -> bool:
    """Handle both provider scalar and list representations for CIDR blocks."""
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return any(cidr in OPEN_CIDRS for cidr in value)
    return value in OPEN_CIDRS


def _ports_in_range(props: Mapping[str, Any]) -> set[int]:
    """Return tracked sensitive ports within the rule's from/to range."""
    protocol = props.get("ipProtocol", props.get("protocol"))
    if isinstance(protocol, str):
        protocol = protocol.lower()
    if protocol in (-1, "-1", "all"):
        return set(SENSITIVE_PORTS)

    from_port = props.get("fromPort")
    to_port = props.get("toPort")
    if not isinstance(from_port, int) or not isinstance(to_port, int):
        return set()
    return {port for port in SENSITIVE_PORTS if from_port <= port <= to_port}


def _truthy(value: object) -> bool:
    """Normalize the common Pulumi representations of true-ish values."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return False


def _string_value(value: object) -> str | None:
    """Return a stripped string or None when no stable value is available."""
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None
