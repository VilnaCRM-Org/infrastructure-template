"""Integration-level guardrail contracts for Pulumi environment metadata."""

from __future__ import annotations

import re

import pytest
from app.environment import _resolve_config_value
from app.guardrails import validate_environment_name, validate_service_name


def test_resolve_config_value_preserves_explicit_configured_and_default_paths() -> None:
    """Keep resolution semantics stable for explicit, configured, and default values."""
    assert _resolve_config_value("prod", "staging", default="dev") == "prod"
    assert _resolve_config_value(None, "staging", default="dev") == "staging"
    assert _resolve_config_value(None, None, default="dev") == "dev"


@pytest.mark.parametrize(
    ("validator", "value", "message"),
    [
        (validate_environment_name, "", "environment must not be empty"),
        (
            validate_environment_name,
            " qa ",
            "environment must not contain surrounding whitespace",
        ),
        (
            validate_service_name,
            "Billing_API",
            "service name must use lowercase letters, digits, and hyphens only",
        ),
    ],
)
def test_identifier_guardrails_reject_invalid_integration_inputs(
    validator, value: str, message: str
) -> None:
    """Exercise invalid metadata branches in the integration battery as well."""
    with pytest.raises(ValueError, match=rf"^{re.escape(message)}\.$"):
        validator(value)
