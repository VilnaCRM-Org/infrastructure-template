"""Structural tests for release automation and Dockerfile hardening."""

from pathlib import Path
import re

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"
DOCKERFILE = PROJECT_ROOT / "Dockerfile"
SECRETS_DOC = PROJECT_ROOT / "docs" / "github-actions-secrets.md"
BATS_FILE = PROJECT_ROOT / "tests" / "unit" / "make_targets.bats"
RELEASE_WORKFLOWS = ("autorelease.yml", "autoprerelase.yml")


def _triggers(workflow: dict) -> dict:
    return workflow.get("on", workflow.get(True, {}))


def _release_job(workflow: dict, *, workflow_name: str) -> dict:
    for job in workflow["jobs"].values():
        step_names = {step.get("name") for step in job.get("steps", [])}
        if "Create Release" in step_names:
            return job
    raise AssertionError(f"Create Release step not found in {workflow_name}")


def _phony_targets() -> set[str]:
    """Extract public phony targets from the repository Makefile."""
    makefile_text = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")
    phony_match = re.search(
        r"^\.PHONY:\s*(.+?)(?=^\S|\Z)", makefile_text, flags=re.MULTILINE | re.DOTALL
    )
    assert phony_match is not None, "Expected a .PHONY declaration in Makefile"

    phony_targets = phony_match.group(1).replace("\\\n", " ")
    return {target for target in phony_targets.split() if target}


def test_release_workflows_use_repo_token_with_github_token_fallback() -> None:
    """Keep the release workflows aligned with the documented secret contract."""
    secrets_doc = SECRETS_DOC.read_text(encoding="utf-8")

    assert "fall back to `GITHUB_TOKEN`" in secrets_doc

    for workflow_name in RELEASE_WORKFLOWS:
        workflow = yaml.safe_load(
            (WORKFLOWS_DIR / workflow_name).read_text(encoding="utf-8")
        )
        release_job = _release_job(workflow, workflow_name=workflow_name)
        steps = release_job["steps"]

        assert (
            release_job["env"]["RELEASE_TOKEN"]
            == "${{ secrets.REPO_GITHUB_TOKEN || secrets.GITHUB_TOKEN }}"
        )
        assert any(step.get("name") == "Create Release" for step in steps)

        if workflow_name in {"autorelease.yml", "autoprerelase.yml"}:
            assert release_job["timeout-minutes"] == 10


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
    phony_targets = _phony_targets()
    expected_invocations = []

    for target in sorted(phony_targets):
        if target == "help":
            expected_invocations.append("make help")
        elif target == "all":
            expected_invocations.append("make all")
        elif target == "pulumi":
            expected_invocations.append('make -n pulumi ARGS="version"')
        else:
            expected_invocations.append(f"make -n {target}")

    for invocation in expected_invocations:
        assert invocation in bats_text


def test_local_battery_workflow_mirrors_make_test() -> None:
    """Ensure GitHub Actions exercises the aggregate local validation command."""
    workflow = yaml.safe_load(
        (WORKFLOWS_DIR / "pulumi-local.yml").read_text(encoding="utf-8")
    )
    triggers = _triggers(workflow)
    jobs = workflow["jobs"]

    assert "local_battery" in jobs

    local_job = jobs["local_battery"]
    step_names = [step.get("name") for step in local_job["steps"]]

    assert triggers["push"]["branches"] == ["main"]
    assert "pull_request" in triggers
    assert local_job["timeout-minutes"] == 30
    assert "Prepare Docker context" in step_names
    assert "Run aggregate local battery inside Docker" in step_names
    assert local_job["steps"][-1]["run"] == "make test"


def test_bats_workflow_runs_on_push_and_pull_request() -> None:
    """Keep the CLI regression suite aligned with other local-only checks."""
    workflow = yaml.safe_load(
        (WORKFLOWS_DIR / "bats-tests.yml").read_text(encoding="utf-8")
    )
    triggers = _triggers(workflow)

    assert triggers["push"]["branches"] == ["main"]
    assert "pull_request" in triggers
