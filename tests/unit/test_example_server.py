"""Unit tests for the ExampleServer Pulumi component."""

import asyncio
import runpy
import sys
from collections.abc import Callable, Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import patch

import pulumi
from pulumi.runtime import mocks, settings, stack

from app.server import ExampleServer


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PULUMI_MAIN = PROJECT_ROOT / "pulumi" / "__main__.py"


class SimpleMocks(mocks.Mocks):
    """Pulumi mocks that synthesize EC2-like outputs for unit tests."""

    def new_resource(self, args: mocks.MockResourceArgs) -> tuple[str, dict]:
        state = dict(args.inputs)
        state.setdefault("public_ip", "203.0.113.10")
        state.setdefault("private_ip", "10.0.0.10")
        state.setdefault("publicIp", "203.0.113.10")
        state.setdefault("privateIp", "10.0.0.10")
        return f"{args.name}_id", state

    def call(self, args: mocks.MockCallArgs) -> dict:
        return args.inputs


def _run_pulumi_program(program: Callable[[], None]) -> None:
    """Execute a Pulumi program with deterministic mocks."""
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
    *,
    required_values: dict[str, str] | None = None,
    optional_values: dict[str, str] | None = None,
) -> Iterator[None]:
    """Patch Pulumi config reads for deterministic tests."""
    required_values = required_values or {"amiId": "ami-default"}
    optional_values = optional_values or {}

    with ExitStack() as exit_stack:
        config_patch = exit_stack.enter_context(patch("app.server.pulumi.Config"))
        config_instance = config_patch.return_value
        config_instance.require.side_effect = lambda key: required_values[key]
        config_instance.get.side_effect = lambda key, default=None: optional_values.get(
            key, default
        )
        yield


def test_instance_type_defaults_to_t2_micro() -> None:
    """Default to the smallest example instance type when config omits it."""

    def program() -> None:
        server = ExampleServer("unit")
        pulumi.export("instanceType", server.instance_type)
        pulumi.export("instanceTags", server.tags)
        _assert_output_value(server.ami_id, "ami-unit")
        _assert_output_value(server.instance_type, "t2.micro")
        _assert_output_value(server.tags, {"Name": "ExampleAppServerInstance"})

    with mocked_pulumi_context(required_values={"amiId": "ami-unit"}):
        _run_pulumi_program(program)


def test_config_values_override_optional_defaults() -> None:
    """Use optional config when callers do not pass explicit overrides."""

    def program() -> None:
        server = ExampleServer("unit")
        pulumi.export("instancePublicIp", server.instance_public_ip)
        _assert_output_value(server.instance_type, "t3.micro")
        _assert_output_value(server.tags, {"Name": "BillingServer"})
        _assert_output_value(server.instance_public_ip, "203.0.113.10")

    with mocked_pulumi_context(
        required_values={"amiId": "ami-config"},
        optional_values={"instanceType": "t3.micro", "nameTag": "BillingServer"},
    ):
        _run_pulumi_program(program)


def test_explicit_arguments_take_precedence_over_config() -> None:
    """Honor explicit component arguments before falling back to config."""

    def program() -> None:
        server = ExampleServer(
            "unit",
            ami_id="ami-explicit",
            instance_type="t3.small",
            name_tag="ExplicitName",
        )
        pulumi.export("instancePrivateIp", server.instance_private_ip)
        _assert_output_value(server.ami_id, "ami-explicit")
        _assert_output_value(server.instance_type, "t3.small")
        _assert_output_value(server.tags, {"Name": "ExplicitName"})
        _assert_output_value(server.instance_private_ip, "10.0.0.10")

    with mocked_pulumi_context(
        required_values={"amiId": "ami-config"},
        optional_values={"instanceType": "t3.micro", "nameTag": "ConfigName"},
    ):
        _run_pulumi_program(program)


def test_component_registers_expected_type_token() -> None:
    """Pass the expected type token into the public ComponentResource API."""
    captured: dict[str, tuple[str, str]] = {}
    original_init = pulumi.ComponentResource.__init__

    def tracked_init(
        self: pulumi.ComponentResource,
        type_token: str,
        name: str,
        props: object = None,
        opts: object = None,
        *args: object,
        **kwargs: object,
    ) -> None:
        if isinstance(self, ExampleServer):
            captured["component"] = (type_token, name)
        original_init(self, type_token, name, props, opts, *args, **kwargs)

    def program() -> None:
        server = ExampleServer("unit")
        pulumi.export("instanceId", server.instance_id)

    with mocked_pulumi_context(required_values={"amiId": "ami-unit"}):
        with patch.object(pulumi.ComponentResource, "__init__", new=tracked_init):
            _run_pulumi_program(program)

    assert captured.get("component") == (
        "infrastructure-template:compute:ExampleServer",
        "unit",
    )


def test_register_outputs_maps_expected_keys() -> None:
    """Register outputs for the public component contract consistently."""
    original_register = pulumi.ComponentResource.register_outputs

    def program() -> None:
        server = ExampleServer(
            "unit",
            ami_id="ami-explicit",
            instance_type="t3.small",
            name_tag="ExplicitName",
        )
        pulumi.export("instanceId", server.instance_id)

    with patch.object(
        pulumi.ComponentResource,
        "register_outputs",
        autospec=True,
        wraps=original_register,
    ) as mock_register:
        _run_pulumi_program(program)

    example_server_calls = [
        register_call
        for register_call in mock_register.call_args_list
        if isinstance(register_call.args[0], ExampleServer)
    ]

    assert example_server_calls

    registered_outputs = example_server_calls[-1].args[1]

    assert set(registered_outputs) == {
        "amiId",
        "instanceId",
        "instanceType",
        "instancePublicIp",
        "instancePrivateIp",
        "tags",
    }


def test_main_exports_expected_outputs() -> None:
    """Execute the Pulumi entrypoint and validate exported outputs."""

    def program() -> None:
        sys.path.insert(0, str(PROJECT_ROOT / "pulumi"))
        try:
            module_globals = runpy.run_path(str(PULUMI_MAIN))
        finally:
            sys.path.pop(0)

        server = module_globals["server"]
        _assert_output_value(server.ami_id, "ami-main")
        _assert_output_value(server.instance_type, "t3.nano")
        _assert_output_value(server.tags, {"Name": "MainProgramServer"})
        _assert_output_value(server.instance_id, "app-server_id")

    with mocked_pulumi_context(
        required_values={"amiId": "ami-main"},
        optional_values={"instanceType": "t3.nano", "nameTag": "MainProgramServer"},
    ):
        _run_pulumi_program(program)


def test_main_prefers_optional_ami_id_config_when_available() -> None:
    """Use the optional amiId config path before falling back to require()."""

    def program() -> None:
        sys.path.insert(0, str(PROJECT_ROOT / "pulumi"))
        try:
            module_globals = runpy.run_path(str(PULUMI_MAIN))
        finally:
            sys.path.pop(0)

        server = module_globals["server"]
        _assert_output_value(server.ami_id, "ami-optional")
        _assert_output_value(server.instance_type, "t3.micro")
        _assert_output_value(server.tags, {"Name": "OptionalAmiServer"})

    with mocked_pulumi_context(
        required_values={"amiId": "ami-required"},
        optional_values={
            "amiId": "ami-optional",
            "instanceType": "t3.micro",
            "nameTag": "OptionalAmiServer",
        },
    ):
        _run_pulumi_program(program)
