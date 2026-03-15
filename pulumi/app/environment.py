"""Pulumi component that exports shared environment and tagging metadata."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Optional

import pulumi
from app.guardrails import validate_environment_name, validate_service_name

__all__ = ["EnvironmentSettings", "resolve_config_value"]


def _stack_parts_from_outputs(parts: Sequence[str]) -> tuple[str, str]:
    """Narrow Pulumi's list-shaped Output.all result to a stable tuple."""
    return parts[0], parts[1]


def _stack_tag_from_parts(parts: tuple[str, str]) -> str:
    """Build the exported stack tag from the service and environment names."""
    return f"{parts[0]}-{parts[1]}"


def _default_tags_from_parts(parts: tuple[str, str]) -> dict[str, str]:
    """Build the default Pulumi tags shared by stack resources."""
    return {"Project": parts[0], "Environment": parts[1]}


def resolve_config_value(
    explicit: str | None, configured: str | None, *, default: str
) -> str:
    """Preserve intentionally empty config values so guardrails can reject them."""
    if explicit is not None:
        return explicit
    if configured is not None:
        return configured
    return default


class EnvironmentSettings(pulumi.ComponentResource):
    """Expose shared environment metadata for the rest of the Pulumi program."""

    def __init__(
        self,
        name: str,
        *,
        environment: Optional[str] = None,
        service_name: Optional[str] = None,
        opts: Optional[pulumi.ResourceOptions] = None,
    ) -> None:
        """Create the component and resolve environment/service configuration."""
        super().__init__(
            "infrastructure-template:core:EnvironmentSettings", name, None, opts
        )

        config = pulumi.Config()

        resolved_environment = validate_environment_name(
            resolve_config_value(
                environment,
                config.get("environment"),
                default="dev",
            )
        )

        resolved_service = validate_service_name(
            resolve_config_value(
                service_name,
                config.get("serviceName"),
                default=pulumi.get_project(),
            )
        )

        self.environment = pulumi.Output.from_input(resolved_environment)
        self.service_name = pulumi.Output.from_input(resolved_service)

        stack_parts: pulumi.Output[tuple[str, str]] = pulumi.Output.all(
            self.service_name, self.environment
        ).apply(_stack_parts_from_outputs)
        self.stack_tag = stack_parts.apply(_stack_tag_from_parts)

        self.default_tags = stack_parts.apply(_default_tags_from_parts)

        self.register_outputs(
            {
                "environment": self.environment,
                "serviceName": self.service_name,
                "stackTag": self.stack_tag,
                "defaultTags": self.default_tags,
            }
        )
