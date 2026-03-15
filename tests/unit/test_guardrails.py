"""Unit tests for Pulumi input guardrails."""

import re

import pytest
from app.guardrails import validate_environment_name, validate_service_name


def test_validate_environment_name_accepts_stable_slug() -> None:
    """Accept lowercase slugs that are safe for exports and tags."""
    assert validate_environment_name("dev") == "dev"


def test_validate_service_name_accepts_stable_slug() -> None:
    """Accept lowercase service names built from digits and hyphens."""
    assert validate_service_name("billing-api2") == "billing-api2"


@pytest.mark.parametrize(
    ("validator", "value", "message"),
    [
        (validate_environment_name, 1, "environment must be a string"),
        (validate_environment_name, "", "environment must not be empty"),
        (
            validate_environment_name,
            " dev ",
            "environment must not contain surrounding whitespace",
        ),
        (
            validate_service_name,
            "Billing_API",
            "service name must use lowercase letters, digits, and hyphens only",
        ),
    ],
)
def test_identifier_guardrails_reject_invalid_values(
    validator, value: object, message: str
) -> None:
    """Reject empty, padded, and malformed identifiers."""
    with pytest.raises(ValueError, match=rf"^{re.escape(message)}\.$"):
        validator(value)
