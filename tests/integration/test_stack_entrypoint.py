"""Stack-level smoke tests for the Pulumi entrypoint."""

import asyncio
import runpy
import sys
from pathlib import Path
from unittest.mock import patch

from pulumi.runtime import mocks, settings, stack


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PULUMI_MAIN = PROJECT_ROOT / "pulumi" / "__main__.py"


class SmokeMocks(mocks.Mocks):
    """Pulumi mocks that return deterministic EC2 outputs for stack tests."""

    def new_resource(self, args: mocks.MockResourceArgs) -> tuple[str, dict]:
        state = dict(args.inputs)
        state.setdefault("public_ip", "198.51.100.24")
        state.setdefault("private_ip", "10.0.1.24")
        state.setdefault("publicIp", "198.51.100.24")
        state.setdefault("privateIp", "10.0.1.24")
        return f"{args.name}_id", state

    def call(self, args: mocks.MockCallArgs) -> dict:
        return args.inputs


def test_stack_entrypoint_executes_with_pulumi_mocks() -> None:
    """Exercise the real Pulumi entrypoint to catch wiring regressions."""
    captured: dict[str, object] = {}
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    try:
        smoke_mocks = SmokeMocks()
        monitor = mocks.MockMonitor(smoke_mocks)
        mocks.set_mocks(
            smoke_mocks,
            project="infrastructure-template",
            stack="integration",
            monitor=monitor,
        )

        def program() -> None:
            sys.path.insert(0, str(PROJECT_ROOT / "pulumi"))
            try:
                module_globals = runpy.run_path(str(PULUMI_MAIN))
            finally:
                sys.path.pop(0)

            server = module_globals["server"]
            server.instance_type.apply(
                lambda value: captured.setdefault("instance_type", value)
            )
            server.tags.apply(lambda value: captured.setdefault("tags", value))
            server.instance_public_ip.apply(
                lambda value: captured.setdefault("public_ip", value)
            )
            server.instance_private_ip.apply(
                lambda value: captured.setdefault("private_ip", value)
            )

        with patch("app.server.pulumi.Config") as config_patch:
            config_instance = config_patch.return_value
            config_instance.require.side_effect = lambda key: {
                "amiId": "ami-integration"
            }[key]
            config_instance.get.side_effect = lambda key, default=None: {
                "instanceType": "t3.small",
                "nameTag": "IntegrationServer",
            }.get(key, default)
            loop.run_until_complete(stack.run_pulumi_func(program))

        assert captured["instance_type"] == "t3.small"
        assert captured["tags"] == {"Name": "IntegrationServer"}
        assert captured["public_ip"] == "198.51.100.24"
        assert captured["private_ip"] == "10.0.1.24"
    finally:
        settings.reset_options(project=None, stack=None)
        loop.close()
        asyncio.set_event_loop(None)
