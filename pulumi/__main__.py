"""Pulumi entrypoint that exports baseline stack metadata."""

import pulumi
from pulumi.runtime import mocks, settings as runtime_settings

from app.environment import EnvironmentSettings
from app.server import ExampleServer


def _resolve_example_server_ami_id() -> str | None:
    """Resolve an AMI for the example server when the entrypoint should expose it."""
    config = pulumi.Config()
    configured_ami_id = config.get("amiId")

    if isinstance(configured_ami_id, str) and configured_ami_id:
        return configured_ami_id

    if isinstance(runtime_settings.get_monitor(), mocks.MockMonitor):
        required_ami_id = config.require("amiId")
        if isinstance(required_ami_id, str) and required_ami_id:
            return required_ami_id

    return None


settings = EnvironmentSettings("environment-settings")
example_server_ami_id = _resolve_example_server_ami_id()
server = (
    ExampleServer("example-server", ami_id=example_server_ami_id)
    if example_server_ami_id is not None
    else None
)

pulumi.export("environment", settings.environment)
pulumi.export("serviceName", settings.service_name)
pulumi.export("stackTag", settings.stack_tag)
pulumi.export("defaultTags", settings.default_tags)

if server is not None:
    pulumi.export("instance_id", server.instance_id)
    pulumi.export("instance_public_ip", server.instance_public_ip)
    pulumi.export("instance_private_ip", server.instance_private_ip)
    pulumi.export("instance_type", server.instance_type)
    pulumi.export("instance_tags", server.tags)
