"""Tests for the Pulumi project manifest."""

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PULUMI_MANIFEST = PROJECT_ROOT / "pulumi" / "Pulumi.yaml"
POLICY_MANIFEST = PROJECT_ROOT / "policy" / "PulumiPolicy.yaml"
POLICY_REQUIREMENTS = PROJECT_ROOT / "policy" / "requirements.txt"


def test_manifest_declares_python_runtime() -> None:
    """Ensure the Pulumi manifest declares the expected runtime and project name."""
    manifest = yaml.safe_load(PULUMI_MANIFEST.read_text(encoding="utf-8"))

    assert manifest["runtime"]["name"] == "python"
    assert manifest["name"] == "infrastructure-template"


def test_policy_pack_manifest_declares_python_runtime() -> None:
    """Ensure the policy pack advertises the expected Python runtime contract."""
    manifest = yaml.safe_load(POLICY_MANIFEST.read_text(encoding="utf-8"))

    assert manifest["runtime"]["name"] == "python"
    assert (
        manifest["runtime"]["options"]["virtualenv"]
        == "/home/dev/.venvs/infrastructure-template"
    )
    assert "guardrails" in manifest["description"]
    assert "pulumi>=" in POLICY_REQUIREMENTS.read_text(encoding="utf-8")
    assert "pulumi-policy" in POLICY_REQUIREMENTS.read_text(encoding="utf-8")
