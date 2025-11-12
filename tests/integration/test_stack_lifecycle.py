from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pulumi.automation as auto


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PULUMI_WORKDIR = PROJECT_ROOT / "pulumi"


def _stack_name() -> str:
    return f"it-{uuid.uuid4().hex[:8]}"


def _pulumi_command() -> auto.PulumiCommand:
    return auto.PulumiCommand(
        command=sys.executable,
        args=["-m", "pulumi"],
    )


def _workspace_options() -> auto.LocalWorkspaceOptions:
    return auto.LocalWorkspaceOptions(pulumi_command=_pulumi_command())


def test_pulumi_stack_preview_and_up_cycle() -> None:
    stack = auto.create_or_select_stack(
        stack_name=_stack_name(),
        work_dir=str(PULUMI_WORKDIR),
        opts=_workspace_options(),
    )
    stack.set_config("environment", auto.ConfigValue(value="integration"))
    stack.set_config("serviceName", auto.ConfigValue(value="integration-test"))

    try:
        preview_result = stack.preview()
        assert preview_result.change_summary is not None

        up_result = stack.up()

        assert up_result.outputs["stackTag"].value == "integration-test-integration"
        assert up_result.outputs["serviceName"].value == "integration-test"
        assert up_result.outputs["environment"].value == "integration"
    finally:
        stack.destroy(on_output=None)
        stack.workspace.remove_stack(stack.name)
