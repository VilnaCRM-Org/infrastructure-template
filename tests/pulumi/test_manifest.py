"""Structural tests for the Pulumi project manifest."""

from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PULUMI_MANIFEST = PROJECT_ROOT / "pulumi" / "Pulumi.yaml"
PULUMI_EXAMPLE = PROJECT_ROOT / "pulumi" / "Pulumi.example.yaml"


def test_manifest_declares_python_runtime_and_template_name() -> None:
    """Keep the manifest aligned with the repository identity."""
    manifest = yaml.safe_load(PULUMI_MANIFEST.read_text(encoding="utf-8"))

    assert manifest["name"] == "infrastructure-template"
    assert manifest["runtime"]["name"] == "python"
    assert manifest["runtime"]["options"]["toolchain"] == "poetry"


def test_example_stack_uses_template_config_namespace() -> None:
    """Ensure example config keys match the Pulumi project name."""
    manifest = yaml.safe_load(PULUMI_MANIFEST.read_text(encoding="utf-8"))
    stack_example = yaml.safe_load(PULUMI_EXAMPLE.read_text(encoding="utf-8"))

    config_keys = set(stack_example["config"])

    assert f'{manifest["name"]}:amiId' in config_keys
    assert f'{manifest["name"]}:instanceType' in config_keys
    assert f'{manifest["name"]}:nameTag' in config_keys
