"""Structural tests for the broader CI quality-gate system."""

from __future__ import annotations

import re
from pathlib import Path

import tomllib
import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"
PYPROJECT = PROJECT_ROOT / "pyproject.toml"
DOCS_INDEX = PROJECT_ROOT / "docs" / "README.md"
ROOT_README = PROJECT_ROOT / "README.md"
QUALITY_DOC = PROJECT_ROOT / "docs" / "ci-quality-gates.md"
ACTION_SHA_REF = re.compile(r"^[^@]+@[0-9a-f]{40}$")


def _workflow(name: str) -> dict:
    """Load a workflow YAML document from disk."""
    return yaml.safe_load((WORKFLOWS_DIR / name).read_text(encoding="utf-8"))


def _triggers(workflow: dict) -> dict:
    """Normalize the GitHub Actions `on` key when YAML parses it as a boolean."""
    return workflow.get("on", workflow.get(True, {}))


def test_pyproject_declares_quality_tooling_contracts() -> None:
    """Keep the repo-local analyzer configuration explicit and discoverable."""
    data = tomllib.loads(PYPROJECT.read_text(encoding="utf-8"))
    dev_dependencies = set(data["dependency-groups"]["dev"])
    ruff = data["tool"]["ruff"]["lint"]
    deptry = data["tool"]["deptry"]
    importlinter = data["tool"]["importlinter"]

    expected_tools = {
        "bandit[toml]>=1.8,<2",
        "cyclonedx-bom>=4.1,<5",
        "deptry>=0.23,<0.24",
        "docstr-coverage>=2.3,<3",
        "import-linter>=2.4,<3",
        "radon>=5.1,<6",
        "vulture>=2.11,<3",
        "wily>=1.25,<2",
        "xenon>=0.9,<1",
        "yamllint>=1.35,<2",
    }

    assert expected_tools.issubset(dev_dependencies)
    assert "C90" in ruff["select"]
    assert data["tool"]["ruff"]["lint"]["mccabe"]["max-complexity"] == 10
    assert deptry["known_first_party"] == ["app", "policy"]
    assert deptry["package_module_name_map"]["pyyaml"] == ["yaml"]
    assert deptry["package_module_name_map"]["pulumi-policy"] == ["pulumi_policy"]
    assert deptry["per_rule_ignores"]["DEP002"] == ["pulumi-aws"]
    assert importlinter["root_packages"] == ["app", "policy"]
    assert len(importlinter["contracts"]) == 4
    assert data["tool"]["vulture"]["min_confidence"] == 80


def test_security_scan_workflow_covers_repo_hygiene_and_dependency_review() -> None:
    """Keep the blocking security workflow aligned with the new safety gates."""
    workflow = _workflow("security-scans.yml")
    jobs = workflow["jobs"]
    dependency_review_steps = jobs["dependency_review"]["steps"]
    checkout_index = next(
        (
            index
            for index, step in enumerate(dependency_review_steps)
            if step.get("uses", "").startswith("actions/checkout@")
        ),
        None,
    )
    dependency_review_index = next(
        (
            index
            for index, step in enumerate(dependency_review_steps)
            if step.get("uses", "").startswith("actions/dependency-review-action@")
        ),
        None,
    )
    assert checkout_index is not None, "actions/checkout step not found"
    assert dependency_review_index is not None, (
        "actions/dependency-review-action step not found"
    )

    assert "bandit" in jobs
    assert "dependency_review" in jobs
    assert "yamllint" in jobs
    assert "shell_hygiene" in jobs
    assert "hadolint" in jobs
    assert jobs["bandit"]["timeout-minutes"] == 10
    assert (
        jobs["dependency_review"]["if"] == "${{ github.event_name == 'pull_request' }}"
    )
    assert jobs["yamllint"]["timeout-minutes"] == 10
    assert jobs["shell_hygiene"]["timeout-minutes"] == 10
    assert jobs["hadolint"]["timeout-minutes"] == 10
    assert any(
        step.get("run") == "make test-bandit" for step in jobs["bandit"]["steps"]
    )
    assert any(
        step.get("run") == "make test-yaml" for step in jobs["yamllint"]["steps"]
    )
    assert any(
        step.get("run") == "make test-shell" for step in jobs["shell_hygiene"]["steps"]
    )
    assert any(
        step.get("run") == "make test-dockerfile" for step in jobs["hadolint"]["steps"]
    )
    assert checkout_index < dependency_review_index
    assert any(
        step.get("uses", "").startswith("actions/dependency-review-action@")
        for step in dependency_review_steps
    )


def test_nightly_quality_workflow_generates_reports_and_attestation() -> None:
    """Keep scheduled quality monitoring and SBOM provenance wired into CI."""
    workflow = _workflow("nightly-quality.yml")
    jobs = workflow["jobs"]
    triggers = _triggers(workflow)
    sbom_uses = [step.get("uses") for step in jobs["sbom"]["steps"] if step.get("uses")]
    upload_steps = [
        step
        for job in jobs.values()
        for step in job.get("steps", [])
        if step.get("uses", "").startswith("actions/upload-artifact@")
    ]
    maintainability_checkout = jobs["maintainability_trends"]["steps"][0]

    assert "schedule" in triggers
    assert "workflow_dispatch" in triggers
    assert jobs["maintainability_trends"]["timeout-minutes"] == 20
    assert jobs["dead_code"]["timeout-minutes"] == 15
    assert jobs["docstrings"]["timeout-minutes"] == 15
    assert jobs["sbom"]["timeout-minutes"] == 15
    assert jobs["docstrings"]["name"] == "Docstring Coverage"
    assert maintainability_checkout["with"]["fetch-depth"] == 0
    assert jobs["sbom"]["permissions"] == {
        "attestations": "write",
        "contents": "read",
        "id-token": "write",
    }
    assert upload_steps
    assert all(
        step.get("with", {}).get("if-no-files-found") == "error"
        for step in upload_steps
    )
    assert any(
        step.get("run") == "make report-maintainability-trends"
        for step in jobs["maintainability_trends"]["steps"]
    )
    assert any(
        step.get("run") == "make report-dead-code"
        for step in jobs["dead_code"]["steps"]
    )
    assert any(
        step.get("run") == "make report-docstrings"
        for step in jobs["docstrings"]["steps"]
    )
    assert any(
        step.get("with", {}).get("path") == ".artifacts/quality/docstr-coverage.txt"
        for step in jobs["docstrings"]["steps"]
    )
    assert any(step.get("run") == "make report-sbom" for step in jobs["sbom"]["steps"])
    assert any("actions/upload-artifact@" in uses for uses in sbom_uses)
    assert any("actions/attest-build-provenance@" in uses for uses in sbom_uses)


def test_quality_docs_and_configs_are_present_and_indexed() -> None:
    """Require operator-facing docs and linter configs for the quality system."""
    docs_index = DOCS_INDEX.read_text(encoding="utf-8")
    root_readme = ROOT_README.read_text(encoding="utf-8")
    content = QUALITY_DOC.read_text(encoding="utf-8")
    yamllint_config = yaml.safe_load(
        (PROJECT_ROOT / ".yamllint.yml").read_text(encoding="utf-8")
    )
    hadolint_config = (PROJECT_ROOT / ".hadolint.yaml").read_text(encoding="utf-8")
    makefile = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")
    dockerfile = (PROJECT_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert QUALITY_DOC.exists()
    assert (PROJECT_ROOT / ".yamllint.yml").exists()
    assert (PROJECT_ROOT / ".hadolint.yaml").exists()
    assert "ci-quality-gates.md" in docs_index
    assert "docs/ci-quality-gates.md" in root_readme
    assert "branch coverage" in content
    assert "Import Linter" in content
    assert "Deptry" in content
    assert "Dependency Review" in content
    assert "Bandit" in content
    assert "Wily" in content
    assert "SBOM" in content
    assert "artifact attestation" in content
    assert ".github/workflows/" not in yamllint_config["ignore"]
    assert yamllint_config["rules"]["truthy"]["check-keys"] is False
    assert ".github/workflows" in makefile
    assert "DL3008" not in hadolint_config
    assert dockerfile.count("# hadolint ignore=DL3008") >= 2


def test_quality_related_actions_are_pinned_to_full_shas() -> None:
    """Avoid mutable action references in the new quality workflows."""
    workflow_names = (
        "python-quality.yml",
        "security-scans.yml",
        "nightly-quality.yml",
    )
    for workflow_name in workflow_names:
        workflow = _workflow(workflow_name)
        for job in workflow["jobs"].values():
            for step in job.get("steps", []):
                uses = step.get("uses")
                if uses is None:
                    continue
                assert ACTION_SHA_REF.match(uses), (
                    f"{workflow_name} must pin `{uses}` to a full commit SHA"
                )
