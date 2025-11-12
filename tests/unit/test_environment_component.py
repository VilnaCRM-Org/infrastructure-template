from collections.abc import Callable
from unittest.mock import patch

import pulumi
from pulumi.runtime import mocks, settings, stack, sync_await

from pulumi.pulumi_app.environment import EnvironmentSettings


class SimpleMocks(mocks.Mocks):
    def new_resource(self, args: mocks.MockResourceArgs) -> tuple[str, dict]:
        return f"{args.name}_id", args.inputs

    def call(self, args: mocks.MockCallArgs) -> dict:
        return args.inputs


def _run_pulumi_program(program: Callable[[], None]) -> dict[str, object]:
    test_mocks = SimpleMocks()
    monitor = mocks.MockMonitor(test_mocks)
    mocks.set_mocks(
        test_mocks,
        project="infrastructure-template",
        stack="unit",
        monitor=monitor,
    )

    try:
        sync_await._sync_await(stack.run_pulumi_func(program))
        root = settings.get_root_resource()
        assert root is not None, "Pulumi Stack was not initialised"

        resolved: dict[str, object] = {}
        for name, value in root.outputs.items():
            if isinstance(value, pulumi.Output):
                resolved[name] = sync_await._sync_await(value.future())
            else:
                resolved[name] = value
        return resolved
    finally:
        settings.reset_options(project="project", stack="stack")


def test_stack_tag_combines_service_and_environment() -> None:
    def program() -> None:
        env_settings = EnvironmentSettings(
            "unit", environment="staging", service_name="billing"
        )
        pulumi.export("stackTag", env_settings.stack_tag)

    outputs = _run_pulumi_program(program)
    assert outputs["stackTag"] == "billing-staging"


def test_default_tags_use_service_and_environment() -> None:
    def program() -> None:
        env_settings = EnvironmentSettings(
            "unit", environment="production", service_name="edge"
        )
        pulumi.export("defaultTags", env_settings.default_tags)

    outputs = _run_pulumi_program(program)
    assert outputs["defaultTags"] == {"Project": "edge", "Environment": "production"}


def test_environment_falls_back_to_config_value() -> None:
    def program() -> None:
        env_settings = EnvironmentSettings("unit")
        pulumi.export("environment", env_settings.environment)
        pulumi.export("serviceName", env_settings.service_name)
        pulumi.export("stackTag", env_settings.stack_tag)
        pulumi.export("defaultTags", env_settings.default_tags)

    with patch("pulumi_app.environment.pulumi.Config") as mock_config:
        config_instance = mock_config.return_value
        config_instance.get.side_effect = lambda key: {"environment": "qa"}.get(key)
        outputs = _run_pulumi_program(program)

    assert outputs["environment"] == "qa"
    assert outputs["serviceName"] == "infrastructure-template"
    assert outputs["stackTag"] == "infrastructure-template-qa"
    assert outputs["defaultTags"] == {
        "Project": "infrastructure-template",
        "Environment": "qa",
    }


def test_environment_defaults_to_dev_when_unset() -> None:
    def program() -> None:
        env_settings = EnvironmentSettings("unit")
        pulumi.export("environment", env_settings.environment)
        pulumi.export("serviceName", env_settings.service_name)
        pulumi.export("stackTag", env_settings.stack_tag)
        pulumi.export("defaultTags", env_settings.default_tags)

    with patch("pulumi_app.environment.pulumi.Config") as mock_config:
        mock_config.return_value.get.return_value = None
        outputs = _run_pulumi_program(program)

    assert outputs["environment"] == "dev"
    assert outputs["serviceName"] == "infrastructure-template"
    assert outputs["stackTag"] == "infrastructure-template-dev"
    assert outputs["defaultTags"] == {
        "Project": "infrastructure-template",
        "Environment": "dev",
    }


def test_service_name_falls_back_to_config_value() -> None:
    def program() -> None:
        env_settings = EnvironmentSettings("unit", environment="qa")
        pulumi.export("serviceName", env_settings.service_name)
        pulumi.export("stackTag", env_settings.stack_tag)
        pulumi.export("defaultTags", env_settings.default_tags)

    with patch("pulumi_app.environment.pulumi.Config") as mock_config:
        config_instance = mock_config.return_value
        config_instance.get.side_effect = lambda key: {"serviceName": "billing"}.get(key)
        outputs = _run_pulumi_program(program)

    assert outputs["serviceName"] == "billing"
    assert outputs["stackTag"] == "billing-qa"
    assert outputs["defaultTags"] == {"Project": "billing", "Environment": "qa"}


def test_service_name_defaults_to_project_name() -> None:
    def program() -> None:
        env_settings = EnvironmentSettings("unit", environment="qa")
        pulumi.export("serviceName", env_settings.service_name)
        pulumi.export("stackTag", env_settings.stack_tag)
        pulumi.export("defaultTags", env_settings.default_tags)

    with patch("pulumi_app.environment.pulumi.Config") as mock_config, patch(
        "pulumi_app.environment.pulumi.get_project", return_value="project-fallback"
    ):
        mock_config.return_value.get.return_value = None
        outputs = _run_pulumi_program(program)

    assert outputs["serviceName"] == "project-fallback"
    assert outputs["stackTag"] == "project-fallback-qa"
    assert outputs["defaultTags"] == {"Project": "project-fallback", "Environment": "qa"}

def test_environment_prefers_explicit_over_config_and_default() -> None:
    """Covers mutation that swaps fallback order for environment."""
    def program():
        env = EnvironmentSettings("unit", environment="explicit")
        pulumi.export("env", env.environment)

    with patch("pulumi_app.environment.pulumi.Config") as mock_config:
        mock_config.return_value.get.return_value = "fromconfig"
        outputs = _run_pulumi_program(program)
    assert outputs["env"] == "explicit"


def test_service_name_prefers_explicit_over_config_and_project() -> None:
    """Covers mutation that swaps fallback order for service name."""
    def program():
        env = EnvironmentSettings("unit", environment="qa", service_name="explicit")
        pulumi.export("serviceName", env.service_name)

    with patch("pulumi_app.environment.pulumi.Config") as mock_config, patch(
        "pulumi_app.environment.pulumi.get_project", return_value="project"
    ):
        mock_config.return_value.get.side_effect = lambda k: {"serviceName": "fromconfig"}.get(k)
        outputs = _run_pulumi_program(program)
    assert outputs["serviceName"] == "explicit"


def test_default_tags_have_correct_keys() -> None:
    """Ensures default_tags dict key order and names are correct."""
    def program():
        env = EnvironmentSettings("unit", environment="qa", service_name="svc")
        pulumi.export("tags", env.default_tags)

    outputs = _run_pulumi_program(program)
    tags = outputs["tags"]
    assert set(tags.keys()) == {"Project", "Environment"}
    assert tags["Project"] == "svc"
    assert tags["Environment"] == "qa"
