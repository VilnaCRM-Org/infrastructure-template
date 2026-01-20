"""Unit tests for the EnvironmentSettings Pulumi component."""

import asyncio
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from unittest.mock import patch

import pulumi
from pulumi.runtime import mocks, settings, stack

from app.environment import EnvironmentSettings


class SimpleMocks(mocks.Mocks):
    """Pulumi mocks that echo inputs for unit testing."""

    def new_resource(self, args: mocks.MockResourceArgs) -> tuple[str, dict]:
        """Return a synthetic resource ID and echo inputs."""
        return f"{args.name}_id", args.inputs

    def call(self, args: mocks.MockCallArgs) -> dict:
        """Return inputs directly for mocked invoke calls."""
        return args.inputs


def _run_pulumi_program(program: Callable[[], None]) -> None:
    """Execute a Pulumi program with mocks."""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        test_mocks = SimpleMocks()
        monitor = mocks.MockMonitor(test_mocks)
        mocks.set_mocks(
            test_mocks,
            project="infrastructure-template",
            stack="unit",
            monitor=monitor,
        )
        loop.run_until_complete(stack.run_pulumi_func(program))
    finally:
        settings.reset_options(project=None, stack=None)
        loop.close()
        asyncio.set_event_loop(None)


def _assert_output_value(output: pulumi.Output, expected: object) -> None:
    """Assert a Pulumi Output resolves to the expected value."""
    def check(value: object) -> None:
        assert value == expected

    output.apply(check)


@contextmanager
def mocked_pulumi_context(
    config_values: dict[str, object] | None = None, *, project_name: str | None = None
) -> Iterator[None]:
    """Patch Pulumi config/project helpers for deterministic tests."""
    config_values = config_values or {}
    with ExitStack() as stack:
        config_patch = stack.enter_context(patch("app.environment.pulumi.Config"))
        config_instance = config_patch.return_value
        config_instance.get.side_effect = lambda key, default=None: config_values.get(key, default)

        if project_name is not None:
            stack.enter_context(
                patch("app.environment.pulumi.get_project", return_value=project_name)
            )

        yield


def test_stack_tag_combines_service_and_environment() -> None:
    """Combine explicit service/environment into a stack tag."""
    def program() -> None:
        """Export the derived stack tag for assertion."""
        env_settings = EnvironmentSettings(
            "unit", environment="staging", service_name="billing"
        )
        pulumi.export("stackTag", env_settings.stack_tag)
        _assert_output_value(env_settings.stack_tag, "billing-staging")

    _run_pulumi_program(program)


def test_default_tags_use_service_and_environment() -> None:
    """Build default tags from explicit service/environment values."""
    def program() -> None:
        """Export default tags for explicit values."""
        env_settings = EnvironmentSettings(
            "unit", environment="production", service_name="edge"
        )
        pulumi.export("defaultTags", env_settings.default_tags)
        _assert_output_value(
            env_settings.default_tags,
            {"Project": "edge", "Environment": "production"},
        )

    _run_pulumi_program(program)


def test_environment_falls_back_to_config_value() -> None:
    """Use the config value when environment is not passed."""
    def program() -> None:
        """Export resolved fields for config-based environment."""
        env_settings = EnvironmentSettings("unit")
        pulumi.export("environment", env_settings.environment)
        pulumi.export("serviceName", env_settings.service_name)
        pulumi.export("stackTag", env_settings.stack_tag)
        pulumi.export("defaultTags", env_settings.default_tags)
        _assert_output_value(env_settings.environment, "qa")
        _assert_output_value(env_settings.service_name, "infrastructure-template")
        _assert_output_value(env_settings.stack_tag, "infrastructure-template-qa")
        _assert_output_value(
            env_settings.default_tags,
            {"Project": "infrastructure-template", "Environment": "qa"},
        )

    with mocked_pulumi_context({"environment": "qa"}):
        _run_pulumi_program(program)


def test_environment_defaults_to_dev_when_unset() -> None:
    """Default environment to dev when no config is set."""
    def program() -> None:
        """Export resolved fields for default environment."""
        env_settings = EnvironmentSettings("unit")
        pulumi.export("environment", env_settings.environment)
        pulumi.export("serviceName", env_settings.service_name)
        pulumi.export("stackTag", env_settings.stack_tag)
        pulumi.export("defaultTags", env_settings.default_tags)
        _assert_output_value(env_settings.environment, "dev")
        _assert_output_value(env_settings.service_name, "infrastructure-template")
        _assert_output_value(env_settings.stack_tag, "infrastructure-template-dev")
        _assert_output_value(
            env_settings.default_tags,
            {"Project": "infrastructure-template", "Environment": "dev"},
        )

    with mocked_pulumi_context():
        _run_pulumi_program(program)


def test_service_name_falls_back_to_config_value() -> None:
    """Use the config value when service name is not passed."""
    def program() -> None:
        """Export resolved fields for config-based service name."""
        env_settings = EnvironmentSettings("unit", environment="qa")
        pulumi.export("serviceName", env_settings.service_name)
        pulumi.export("stackTag", env_settings.stack_tag)
        pulumi.export("defaultTags", env_settings.default_tags)
        _assert_output_value(env_settings.service_name, "billing")
        _assert_output_value(env_settings.stack_tag, "billing-qa")
        _assert_output_value(env_settings.default_tags, {"Project": "billing", "Environment": "qa"})

    with mocked_pulumi_context({"serviceName": "billing"}):
        _run_pulumi_program(program)


def test_service_name_defaults_to_project_name() -> None:
    """Default service name to the Pulumi project name."""
    def program() -> None:
        """Export resolved fields for project-name fallback."""
        env_settings = EnvironmentSettings("unit", environment="qa")
        pulumi.export("serviceName", env_settings.service_name)
        pulumi.export("stackTag", env_settings.stack_tag)
        pulumi.export("defaultTags", env_settings.default_tags)
        _assert_output_value(env_settings.service_name, "project-fallback")
        _assert_output_value(env_settings.stack_tag, "project-fallback-qa")
        _assert_output_value(
            env_settings.default_tags,
            {"Project": "project-fallback", "Environment": "qa"},
        )

    with mocked_pulumi_context(project_name="project-fallback"):
        _run_pulumi_program(program)


def test_component_uses_expected_type_token() -> None:
    """Expose the expected component type token."""
    captured: dict[str, EnvironmentSettings] = {}

    def program() -> None:
        """Capture the component instance for type checks."""
        env_settings = EnvironmentSettings("unit")
        captured["resource"] = env_settings
        pulumi.export("environment", env_settings.environment)

    _run_pulumi_program(program)

    resource = captured.get("resource")
    assert resource is not None, "EnvironmentSettings instance was not created"
    assert getattr(resource, "_type", None) == "infrastructure-template:core:EnvironmentSettings"


def test_register_outputs_maps_component_properties() -> None:
    """Register outputs for component properties consistently."""
    original_register = pulumi.ComponentResource.register_outputs

    def program() -> None:
        """Export component outputs for register_outputs tracking."""
        env_settings = EnvironmentSettings("unit", environment="qa", service_name="svc")
        pulumi.export("stackTag", env_settings.stack_tag)
        pulumi.export("defaultTags", env_settings.default_tags)

    with patch.object(
        pulumi.ComponentResource,
        "register_outputs",
        autospec=True,
        wraps=original_register,
    ) as mock_register:
        _run_pulumi_program(program)

    env_calls = [
        register_call
        for register_call in mock_register.call_args_list
        if isinstance(register_call.args[0], EnvironmentSettings)
    ]
    assert env_calls, "EnvironmentSettings.register_outputs was not invoked"

    resource, outputs = env_calls[0].args
    assert set(outputs.keys()) == {"environment", "serviceName", "stackTag", "defaultTags"}
    assert outputs["environment"] is resource.environment
    assert outputs["serviceName"] is resource.service_name
    assert outputs["stackTag"] is resource.stack_tag
    assert outputs["defaultTags"] is resource.default_tags
