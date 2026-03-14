"""Structural tests for release automation and Dockerfile hardening."""

from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"
DOCKERFILE = PROJECT_ROOT / "Dockerfile"
SECRETS_DOC = PROJECT_ROOT / "docs" / "github-actions-secrets.md"
BATS_FILE = PROJECT_ROOT / "tests" / "unit" / "make_targets.bats"
UV_LOCKFILE = PROJECT_ROOT / "uv.lock"
RELEASE_WORKFLOWS = ("autorelease.yml", "autoprerelase.yml")
PULL_REQUEST_WORKFLOW_TIMEOUTS = {
    "bats-tests.yml": {"bats_tests": 15},
    "pulumi-integration.yml": {"integration": 20},
    "pulumi-local.yml": {"local_battery": 45},
    "pulumi-mutation.yml": {"mutation": 20},
    "pulumi-structural.yml": {"structural": 15},
    "pulumi-unit.yml": {"unit": 15},
    "python-quality.yml": {"ruff": 15, "ty": 15},
}
DOCS_INDEX = PROJECT_ROOT / "docs" / "README.md"
ROOT_README = PROJECT_ROOT / "README.md"
PREPARE_SCRIPT = PROJECT_ROOT / "scripts" / "prepare_docker_context.sh"
DETAILED_DOCS = (
    "ci-architecture.md",
    "security-baseline.md",
    "sre-operations.md",
)


def _triggers(workflow: dict) -> dict:
    return workflow.get("on", workflow.get(True, {}))


def _release_job(workflow: dict, *, workflow_name: str) -> dict:
    for job in workflow["jobs"].values():
        step_names = {step.get("name") for step in job.get("steps", [])}
        if "Create Release" in step_names:
            return job
    raise AssertionError(f"Create Release step not found in {workflow_name}")


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
        assert release_job["timeout-minutes"] == 10
        assert workflow["concurrency"]["cancel-in-progress"] is True


def test_dockerfile_pins_base_image_and_verifies_downloads() -> None:
    """Require checksum verification for externally downloaded tooling."""
    dockerfile_text = DOCKERFILE.read_text(encoding="utf-8")

    assert "python:3.11.9-slim-bookworm@" in dockerfile_text
    assert "FROM ${BASE_IMAGE} AS tooling" in dockerfile_text
    assert "FROM ${BASE_IMAGE} AS runtime-base" in dockerfile_text
    assert "TARGETARCH=amd64" in dockerfile_text
    assert "PULUMI_SHA256_AMD64" in dockerfile_text
    assert "PULUMI_SHA256_ARM64" in dockerfile_text
    assert "AWSCLI_SHA256_AMD64" in dockerfile_text
    assert "AWSCLI_SHA256_ARM64" in dockerfile_text
    assert "UV_SHA256_AMD64" in dockerfile_text
    assert "UV_SHA256_ARM64" in dockerfile_text
    assert "BATS_SHA256" in dockerfile_text
    assert "UV_PROJECT_ENVIRONMENT" in dockerfile_text
    assert "PULUMI_PYTHON_CMD" in dockerfile_text
    assert 'AWS_PAGER=""' in dockerfile_text
    assert "PULUMI_HOME" in dockerfile_text
    assert "PULUMI_SKIP_UPDATE_CHECK=true" in dockerfile_text
    assert "PYTHONDONTWRITEBYTECODE=1" in dockerfile_text
    assert "PYTHONUNBUFFERED=1" in dockerfile_text
    assert "uv venv --seed" in dockerfile_text
    assert UV_LOCKFILE.exists()
    assert dockerfile_text.count('case "${TARGETARCH}" in') == 3
    assert "/opt/pulumi/pulumi-language-dotnet" in dockerfile_text
    assert "/usr/local/aws-cli/v2/current/dist/awscli/examples" in dockerfile_text
    assert dockerfile_text.count("sha256sum -c -") >= 4


def test_bats_suite_covers_every_public_make_target() -> None:
    """Keep every public make target locked down by the CLI regression suite."""
    bats_text = BATS_FILE.read_text(encoding="utf-8")
    expected_invocations = [
        "make help",
        "make all",
        "make -n build",
        "make -n ci",
        "make -n doctor",
        "make -n start",
        "make -n pulumi-preview",
        "make -n pulumi-up",
        "make -n pulumi-refresh",
        "make -n pulumi-destroy",
        "make -n sh",
        "make -n down",
        "make -n test-quality",
        "make -n test-ruff",
        "make -n test-ty",
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


def test_local_battery_workflow_mirrors_make_ci() -> None:
    """Ensure GitHub Actions exercises the full PR-equivalent local command."""
    workflow = yaml.safe_load(
        (WORKFLOWS_DIR / "pulumi-local.yml").read_text(encoding="utf-8")
    )
    triggers = _triggers(workflow)
    step_names = [
        step.get("name") for step in workflow["jobs"]["local_battery"]["steps"]
    ]

    assert triggers["push"]["branches"] == ["main"]
    assert "pull_request" in triggers
    assert workflow["jobs"]["local_battery"]["timeout-minutes"] == 45
    assert "Prepare Docker context" in step_names
    assert "Run full CI-equivalent battery inside Docker" in step_names
    assert any(
        step.get("run") == "make ci"
        for step in workflow["jobs"]["local_battery"]["steps"]
    )


def test_ci_workflows_keep_make_entrypoints_in_sync() -> None:
    """Keep each PR validation workflow wired to its corresponding make target."""
    expected_runs = {
        "bats-tests.yml": ["make test-cli"],
        "pulumi-integration.yml": ["make test-integration"],
        "pulumi-local.yml": ["make ci"],
        "pulumi-mutation.yml": ["make test-mutation"],
        "pulumi-structural.yml": ["make test-pulumi"],
        "pulumi-unit.yml": ["make test-unit"],
        "python-quality.yml": ["make test-ruff", "make test-ty"],
    }

    for workflow_name, commands in expected_runs.items():
        workflow = yaml.safe_load(
            (WORKFLOWS_DIR / workflow_name).read_text(encoding="utf-8")
        )
        runs = [
            step.get("run")
            for job in workflow["jobs"].values()
            for step in job.get("steps", [])
            if step.get("run")
        ]

        for command in commands:
            assert any(command in run for run in runs), (
                f"{workflow_name} is missing `{command}`"
            )


def test_ci_workflows_use_guardrails_and_shared_bootstrap() -> None:
    """Require consistent concurrency, timeout, and bootstrap rules in CI."""
    assert PREPARE_SCRIPT.exists()

    for workflow_name, jobs in PULL_REQUEST_WORKFLOW_TIMEOUTS.items():
        workflow = yaml.safe_load(
            (WORKFLOWS_DIR / workflow_name).read_text(encoding="utf-8")
        )
        triggers = _triggers(workflow)

        assert triggers["push"]["branches"] == ["main"]
        assert triggers["pull_request"]["branches"] == ["main"]
        assert workflow["permissions"] == {"contents": "read"}
        assert workflow["defaults"]["run"]["shell"] == "bash"
        assert workflow["concurrency"]["cancel-in-progress"] is True
        assert "${{ github.workflow }}" in workflow["concurrency"]["group"]
        assert (
            "${{ github.event.pull_request.number || github.ref }}"
            in workflow["concurrency"]["group"]
        )

        for job_name, expected_timeout in jobs.items():
            job = workflow["jobs"][job_name]
            assert job["timeout-minutes"] == expected_timeout
            assert any(
                step.get("run") == "./scripts/prepare_docker_context.sh"
                for step in job["steps"]
            ), f"{workflow_name}:{job_name} must use the shared Docker bootstrap"


def test_bats_workflow_runs_on_push_and_pull_request() -> None:
    """Keep the CLI regression suite aligned with other local-only checks."""
    workflow = yaml.safe_load(
        (WORKFLOWS_DIR / "bats-tests.yml").read_text(encoding="utf-8")
    )
    triggers = _triggers(workflow)

    assert triggers["push"]["branches"] == ["main"]
    assert "pull_request" in triggers


def test_quality_workflow_runs_ruff_and_ty_on_push_and_pull_request() -> None:
    """Keep the Rust-based Python quality gates wired into CI."""
    workflow = yaml.safe_load(
        (WORKFLOWS_DIR / "python-quality.yml").read_text(encoding="utf-8")
    )
    triggers = _triggers(workflow)
    jobs = workflow.get("jobs", {})

    assert "ruff" in jobs, "python-quality.yml missing 'ruff' job"
    assert "ty" in jobs, "python-quality.yml missing 'ty' job"

    ruff_runs = [step.get("run") for step in jobs["ruff"]["steps"]]
    ty_runs = [step.get("run") for step in jobs["ty"]["steps"]]

    assert triggers["push"]["branches"] == ["main"]
    assert "pull_request" in triggers
    assert "make test-ruff" in ruff_runs
    assert "make test-ty" in ty_runs


def test_operator_docs_are_present_and_indexed() -> None:
    """Keep the root documentation discoverable from the handbook and README."""
    docs_index = DOCS_INDEX.read_text(encoding="utf-8")
    root_readme = ROOT_README.read_text(encoding="utf-8")

    for doc_name in DETAILED_DOCS:
        assert (PROJECT_ROOT / "docs" / doc_name).exists()
        assert doc_name in docs_index
        assert f"docs/{doc_name}" in root_readme
