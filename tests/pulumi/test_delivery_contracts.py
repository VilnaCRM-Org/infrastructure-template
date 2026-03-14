"""Structural tests for release automation and Dockerfile hardening."""

from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"
DOCKERFILE = PROJECT_ROOT / "Dockerfile"
SECRETS_DOC = PROJECT_ROOT / "docs" / "github-actions-secrets.md"


def test_autorelease_uses_repo_token_with_github_token_fallback() -> None:
    """Keep the workflow aligned with the documented release secret contract."""
    workflow = yaml.safe_load((WORKFLOWS_DIR / "autorelease.yml").read_text(encoding="utf-8"))
    steps = workflow["jobs"]["build"]["steps"]
    secrets_doc = SECRETS_DOC.read_text(encoding="utf-8")

    assert workflow["jobs"]["build"]["env"]["RELEASE_TOKEN"] == "${{ secrets.REPO_GITHUB_TOKEN || secrets.GITHUB_TOKEN }}"
    assert "fall back to `GITHUB_TOKEN`" in secrets_doc
    assert any(step.get("name") == "Create Release" for step in steps)


def test_dockerfile_pins_base_image_and_verifies_downloads() -> None:
    """Require checksum verification for externally downloaded tooling."""
    dockerfile_text = DOCKERFILE.read_text(encoding="utf-8")

    assert "python:3.11.9-slim-bookworm@" in dockerfile_text
    assert "PULUMI_SHA256" in dockerfile_text
    assert "AWSCLI_SHA256" in dockerfile_text
    assert "POETRY_INSTALLER_SHA256" in dockerfile_text
    assert "BATS_SHA256" in dockerfile_text
    assert dockerfile_text.count("sha256sum -c -") >= 4
