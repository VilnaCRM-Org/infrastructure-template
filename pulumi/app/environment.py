from __future__ import annotations

from typing import Optional

import pulumi


def _stack_parts_from_outputs(parts: list[str]) -> tuple[str, str]:
    """Narrow Pulumi's list-shaped Output.all result to a stable tuple."""
    return parts[0], parts[1]


def _stack_tag_from_parts(parts: tuple[str, str]) -> str:
    """Build the exported stack tag from the service and environment names."""
    return f"{parts[0]}-{parts[1]}"


def _default_tags_from_parts(parts: tuple[str, str]) -> dict[str, str]:
    """Build the default Pulumi tags shared by stack resources."""
    return {"Project": parts[0], "Environment": parts[1]}


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

        resolved_environment = environment or config.get("environment") or "dev"

        resolved_service = (
            service_name or config.get("serviceName") or pulumi.get_project()
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
