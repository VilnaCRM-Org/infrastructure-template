"""Pulumi entrypoint that exports baseline stack metadata."""

import pulumi

from app.environment import EnvironmentSettings


settings = EnvironmentSettings("environment-settings")

pulumi.export("environment", settings.environment)
pulumi.export("serviceName", settings.service_name)
pulumi.export("stackTag", settings.stack_tag)
pulumi.export("defaultTags", settings.default_tags)
