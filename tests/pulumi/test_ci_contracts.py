"""Structural tests for CI workflow and Dockerfile hardening."""

from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"
DOCKERFILE = PROJECT_ROOT / "Dockerfile"


def _workflow(name: str) -> dict:
    return yaml.safe_load((WORKFLOWS_DIR / name).read_text(encoding="utf-8"))


def test_preview_workflow_supports_oidc_and_static_credentials() -> None:
    """Keep the preview workflow compatible with both secure auth modes."""
    workflow = _workflow("pulumi-preview.yml")
    job = workflow["jobs"]["preview"]
    step_names = [step.get("name") for step in job["steps"]]

    assert workflow["permissions"]["id-token"] == "write"
    assert workflow["concurrency"]["cancel-in-progress"] is True
    assert "Detect automation credentials" in step_names
    assert "Skip preview when credentials are not configured" in step_names
    assert "Configure AWS Credentials via OIDC" in step_names
    assert "Configure AWS Credentials via static keys" in step_names
    assert (
        job["env"]["AWS_ROLE_TO_ASSUME"]
        == "${{ vars.AWS_ROLE_TO_ASSUME || secrets.AWS_ROLE_TO_ASSUME }}"
    )
    assert job["steps"][-1]["if"] == "${{ steps.credentials.outputs.ready == 'true' }}"


def test_deploy_workflow_serializes_stack_updates() -> None:
    """Prevent concurrent deploys against the same Pulumi stack."""
    workflow = _workflow("pulumi-deploy.yml")
    step_names = [step.get("name") for step in workflow["jobs"]["deploy"]["steps"]]

    assert workflow["permissions"]["id-token"] == "write"
    assert workflow["concurrency"]["cancel-in-progress"] is False
    assert "pulumi-deploy" in workflow["concurrency"]["group"]
    assert "Detect automation credentials" in step_names
    assert "Skip deploy when credentials are not configured" in step_names


def test_super_linter_workflow_stays_read_only() -> None:
    """Avoid write-back behavior during pull request validation."""
    workflow_text = (WORKFLOWS_DIR / "super-linter.yml").read_text(encoding="utf-8")

    assert "FIX_" not in workflow_text
    assert "git commit" not in workflow_text
    assert "persist-credentials: false" in workflow_text


def test_dockerfile_verifies_downloaded_artifacts() -> None:
    """Require checksum verification for third-party CLI downloads."""
    dockerfile_text = DOCKERFILE.read_text(encoding="utf-8")

    assert "PULUMI_SHA256" in dockerfile_text
    assert "AWSCLI_SHA256" in dockerfile_text
    assert "POETRY_INSTALLER_SHA256" in dockerfile_text
    assert dockerfile_text.count("sha256sum -c -") >= 3
    assert "FROM ${BASE_IMAGE}" in dockerfile_text
