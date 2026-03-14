"""Structural tests for release automation and Dockerfile hardening."""

from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"
DOCKERFILE = PROJECT_ROOT / "Dockerfile"
SECRETS_DOC = PROJECT_ROOT / "docs" / "github-actions-secrets.md"
BATS_FILE = PROJECT_ROOT / "tests" / "unit" / "make_targets.bats"


def _triggers(workflow: dict) -> dict:
    return workflow.get("on", workflow.get(True, {}))


def _release_job(workflow: dict) -> dict:
    for job in workflow["jobs"].values():
        step_names = {step.get("name") for step in job.get("steps", [])}
        if "Create Release" in step_names:
            return job
    raise AssertionError("Create Release step not found in autorelease workflow")


def test_autorelease_uses_repo_token_with_github_token_fallback() -> None:
    """Keep the workflow aligned with the documented release secret contract."""
    workflow = yaml.safe_load(
        (WORKFLOWS_DIR / "autorelease.yml").read_text(encoding="utf-8")
    )
    release_job = _release_job(workflow)
    steps = release_job["steps"]
    secrets_doc = SECRETS_DOC.read_text(encoding="utf-8")

    assert (
        release_job["env"]["RELEASE_TOKEN"]
        == "${{ secrets.REPO_GITHUB_TOKEN || secrets.GITHUB_TOKEN }}"
    )
    assert release_job["timeout-minutes"] == 10
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


def test_bats_suite_covers_every_public_make_target() -> None:
    """Keep every public make target locked down by the CLI regression suite."""
    bats_text = BATS_FILE.read_text(encoding="utf-8")
    expected_invocations = [
        "make help",
        "make all",
        "make -n start",
        "make -n pulumi-preview",
        "make -n pulumi-up",
        "make -n pulumi-refresh",
        "make -n pulumi-destroy",
        "make -n sh",
        "make -n down",
        "make -n test-unit",
        "make -n test-integration",
        "make -n test-pulumi",
        "make -n test-mutation",
        "make -n test-cli",
        "make -n test",
        "make -n clean",
    ]

    for invocation in expected_invocations:
        assert invocation in bats_text


def test_local_battery_workflow_mirrors_make_test() -> None:
    """Ensure GitHub Actions exercises the aggregate local validation command."""
    workflow = yaml.safe_load(
        (WORKFLOWS_DIR / "pulumi-local.yml").read_text(encoding="utf-8")
    )
    triggers = _triggers(workflow)
    step_names = [
        step.get("name") for step in workflow["jobs"]["local_battery"]["steps"]
    ]

    assert triggers["push"]["branches"] == ["main"]
    assert "pull_request" in triggers
    assert workflow["jobs"]["local_battery"]["timeout-minutes"] == 30
    assert "Prepare Docker context" in step_names
    assert "Run aggregate local battery inside Docker" in step_names
    assert workflow["jobs"]["local_battery"]["steps"][-1]["run"] == "make test"


def test_bats_workflow_runs_on_push_and_pull_request() -> None:
    """Keep the CLI regression suite aligned with other local-only checks."""
    workflow = yaml.safe_load(
        (WORKFLOWS_DIR / "bats-tests.yml").read_text(encoding="utf-8")
    )
    triggers = _triggers(workflow)

    assert triggers["push"]["branches"] == ["main"]
    assert "pull_request" in triggers
