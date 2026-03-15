"""Structural tests for release automation and repository hardening."""

import os
import re
import stat
import subprocess
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORKFLOWS_DIR = PROJECT_ROOT / ".github" / "workflows"
DOCKERFILE = PROJECT_ROOT / "Dockerfile"
DOCKER_COMPOSE = PROJECT_ROOT / "docker-compose.yml"
SECRETS_DOC = PROJECT_ROOT / "docs" / "github-actions-secrets.md"
BATS_FILE = PROJECT_ROOT / "tests" / "unit" / "make_targets.bats"
UV_LOCKFILE = PROJECT_ROOT / "uv.lock"
RELEASE_WORKFLOWS = ("autorelease.yml", "autoprerelase.yml")
TEMPLATE_SYNC_WORKFLOWS = ("template-sync-app.yml", "template-sync-pat.yml")
PULL_REQUEST_WORKFLOW_TIMEOUTS = {
    "bats-tests.yml": {"bats_tests": 15},
    "pulumi-integration.yml": {"integration": 20},
    "pulumi-local.yml": {"local_battery": 30},
    "pulumi-mutation.yml": {"mutation": 45},
    "pulumi-policy.yml": {"policy": 15},
    "pulumi-structural.yml": {"structural": 15},
    "pulumi-unit.yml": {"unit": 15},
    "python-quality.yml": {"ruff": 15, "ty": 15},
}
DOCS_INDEX = PROJECT_ROOT / "docs" / "README.md"
ROOT_README = PROJECT_ROOT / "README.md"
PREPARE_SCRIPT = PROJECT_ROOT / "scripts" / "prepare_docker_context.sh"
PREPARE_POLICY_SCRIPT = PROJECT_ROOT / "scripts" / "prepare_policy_pack.sh"
DETAILED_DOCS = (
    "ci-architecture.md",
    "pulumi-guardrails.md",
    "security-baseline.md",
    "sre-operations.md",
)
ACTION_SHA_REF = re.compile(r"^[^@]+@[0-9a-f]{40}$")


def _triggers(workflow: dict) -> dict:
    return workflow.get("on", workflow.get(True, {}))


def _release_job(workflow: dict, *, workflow_name: str) -> dict:
    for job in workflow["jobs"].values():
        step_names = {step.get("name") for step in job.get("steps", [])}
        if "Create Release" in step_names:
            return job
    raise AssertionError(f"Create Release step not found in {workflow_name}")


def _checkout_step(steps: list[dict], *, workflow_name: str) -> dict:
    """Return the checkout step without depending on step ordering."""
    for step in steps:
        uses = step.get("uses", "")
        if uses.startswith("actions/checkout@"):
            return step
    raise AssertionError(f"actions/checkout not found in {workflow_name}")


def _run_lines(steps: list[dict]) -> list[str]:
    """Flatten workflow shell snippets into normalized lines for contract checks."""
    lines: list[str] = []
    for step in steps:
        run = step.get("run")
        if not run:
            continue
        lines.extend(line.strip() for line in run.splitlines() if line.strip())
    return lines


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
        assert workflow["concurrency"]["cancel-in-progress"] is False


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
    assert dockerfile_text.count('case "${TARGETARCH}" in') >= 3
    assert "/opt/pulumi/pulumi-language-dotnet" in dockerfile_text
    assert "/usr/local/aws-cli/v2/current/dist/awscli/examples" in dockerfile_text
    assert dockerfile_text.count("sha256sum -c -") >= 4


def test_docker_compose_keeps_workspace_and_credentials_contract() -> None:
    """Keep the local container contract stable for developers and CI."""
    compose = yaml.safe_load(DOCKER_COMPOSE.read_text(encoding="utf-8"))
    service = compose["services"]["pulumi"]

    assert service["build"]["context"] == "."
    assert service["build"]["dockerfile"] == "Dockerfile"
    assert service["build"]["target"] == "${COMPOSE_TARGET:-dev}"
    assert service["build"]["args"]["UID"] == "${UID:-1000}"
    assert service["build"]["args"]["GID"] == "${GID:-1000}"
    assert service["build"]["args"]["USERNAME"] == "dev"
    assert service["working_dir"] == "/workspace"
    assert service["tty"] is True
    assert service["stdin_open"] is True

    volumes = service["volumes"]
    assert any(
        volume["source"] == "." and volume["target"] == "/workspace"
        for volume in volumes
    )
    assert any(
        volume["source"] == "${HOME}/.aws"
        and volume["target"] == "/home/dev/.aws"
        and volume["read_only"] is True
        for volume in volumes
    )

    assert service["env_file"] == [{"path": ".env", "required": False}]
    assert service["environment"] == [
        "PULUMI_ACCESS_TOKEN",
        "PULUMI_BACKEND_URL",
        "PULUMI_CONFIG_PASSPHRASE",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_PROFILE",
        "PYTHONPATH=/workspace/pulumi",
    ]


def test_prepare_docker_context_script_creates_expected_files(tmp_path: Path) -> None:
    """Keep the shared CI/local bootstrap script idempotent and predictable."""
    home_dir = tmp_path / "home"
    repo_dir = tmp_path / "repo"
    home_dir.mkdir()
    repo_dir.mkdir()
    (repo_dir / ".env.empty").write_text(
        "PULUMI_SKIP_UPDATE_CHECK=true\n",
        encoding="utf-8",
    )

    subprocess.run(
        ["bash", str(PREPARE_SCRIPT)],
        check=True,
        cwd=repo_dir,
        env={**os.environ, "HOME": str(home_dir)},
        timeout=30,
    )

    aws_dir = home_dir / ".aws"
    assert aws_dir.is_dir()
    assert stat.S_IMODE(aws_dir.stat().st_mode) == 0o700
    assert (repo_dir / ".env").read_text(encoding="utf-8") == (
        "PULUMI_SKIP_UPDATE_CHECK=true\n"
    )
    assert stat.S_IMODE((repo_dir / ".env").stat().st_mode) == 0o600
    assert (repo_dir / ".pulumi-backend").is_dir()
    assert stat.S_IMODE((repo_dir / ".pulumi-backend").stat().st_mode) == 0o700


def test_prepare_docker_context_script_preserves_existing_env_file(
    tmp_path: Path,
) -> None:
    """Avoid overwriting developer-specific env files during bootstrap."""
    home_dir = tmp_path / "home"
    repo_dir = tmp_path / "repo"
    home_dir.mkdir()
    repo_dir.mkdir()
    (repo_dir / ".env.empty").write_text("DEFAULT=value\n", encoding="utf-8")
    (repo_dir / ".env").write_text("LOCAL=value\n", encoding="utf-8")

    subprocess.run(
        ["bash", str(PREPARE_SCRIPT)],
        check=True,
        cwd=repo_dir,
        env={**os.environ, "HOME": str(home_dir)},
        timeout=30,
    )

    assert (repo_dir / ".env").read_text(encoding="utf-8") == "LOCAL=value\n"
    assert stat.S_IMODE((repo_dir / ".env").stat().st_mode) == 0o600


def test_prepare_docker_context_script_requires_env_template(tmp_path: Path) -> None:
    """Fail clearly when the committed fallback env file is missing."""
    home_dir = tmp_path / "home"
    repo_dir = tmp_path / "repo"
    home_dir.mkdir()
    repo_dir.mkdir()

    result = subprocess.run(
        ["bash", str(PREPARE_SCRIPT)],
        check=False,
        cwd=repo_dir,
        capture_output=True,
        text=True,
        env={**os.environ, "HOME": str(home_dir)},
        timeout=30,
    )

    assert result.returncode != 0
    assert "error: .env.empty not found" in result.stderr


def test_prepare_policy_pack_script_uses_shared_uv_environment() -> None:
    """Keep policy-pack bootstrap aligned with the shared uv-managed interpreter."""
    script_text = PREPARE_POLICY_SCRIPT.read_text(encoding="utf-8")

    assert PREPARE_POLICY_SCRIPT.exists()
    assert 'POLICY_VENV="${POLICY_VENV:-${HOME}/.venvs/infrastructure-template}"' in (
        script_text
    )
    assert 'POLICY_VENV_LINK="${POLICY_DIR}/.venv"' in script_text
    assert 'ln -sfn "${POLICY_VENV}" "${POLICY_VENV_LINK}"' in script_text
    assert 'UV_PROJECT_ENVIRONMENT="${POLICY_VENV}"' in script_text
    assert "uv sync --frozen --all-groups" in script_text
    assert "import pulumi" in script_text
    assert "import pulumi_policy" in script_text


def test_coverage_bearing_make_targets_enforce_full_line_coverage() -> None:
    """Prevent drift in the 100%-coverage contract for Python test suites."""
    makefile_text = (PROJECT_ROOT / "Makefile").read_text(encoding="utf-8")
    coverage_config = (PROJECT_ROOT / ".coveragerc").read_text(encoding="utf-8")

    assert "rm -f .coverage.unit .coverage.unit.*" in makefile_text
    assert "rm -f .coverage.integration .coverage.integration.*" in makefile_text
    assert "rm -f .coverage.policy .coverage.policy.*" in makefile_text
    assert "coverage report --show-missing --include='pulumi/*' --fail-under=100" in (
        makefile_text
    )
    assert (
        "INTEGRATION_COVERAGE_INCLUDE ?= pulumi/__main__.py,pulumi/app/*"
        in makefile_text
    )
    assert (
        "coverage report --show-missing --fail-under=100 "
        "--include='$(INTEGRATION_COVERAGE_INCLUDE)'" in makefile_text
    )
    assert "coverage report --show-missing --include='policy/*' --fail-under=100" in (
        makefile_text
    )
    assert "pulumi/sitecustomize.py" not in coverage_config


def test_bats_suite_covers_every_public_make_target() -> None:
    """Keep every public make target locked down by the CLI regression suite."""
    bats_text = BATS_FILE.read_text(encoding="utf-8")
    expected_invocations = [
        "make help",
        "make all",
        "make -n build",
        "make -n ci",
        "make -n ci-pr",
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
        "make -n test-policy",
        "make -n test-mutation",
        "make -n test-cli",
        "make -n test",
        "make -n clean",
    ]

    for invocation in expected_invocations:
        assert invocation in bats_text


def test_local_battery_workflow_avoids_duplicate_mutation_runs() -> None:
    """Ensure GitHub Actions keeps mutation isolated to the dedicated workflow."""
    workflow = yaml.safe_load(
        (WORKFLOWS_DIR / "pulumi-local.yml").read_text(encoding="utf-8")
    )
    triggers = _triggers(workflow)
    steps = workflow["jobs"]["local_battery"]["steps"]
    step_names = [step.get("name") for step in steps]
    run_lines = _run_lines(steps)

    assert triggers["push"]["branches"] == ["main"]
    assert "pull_request" in triggers
    assert workflow["jobs"]["local_battery"]["timeout-minutes"] == 30
    assert "Prepare Docker context" in step_names
    assert "Run non-mutation PR battery inside Docker" in step_names
    assert any("make ci-pr" in line for line in run_lines)
    assert not any("make ci" == line for line in run_lines)
    assert not any("make test-mutation" in line for line in run_lines)


def test_ci_workflows_keep_make_entrypoints_in_sync() -> None:
    """Keep each PR validation workflow wired to its corresponding make target."""
    expected_runs = {
        "bats-tests.yml": ["make test-cli"],
        "pulumi-integration.yml": ["make test-integration"],
        "pulumi-local.yml": ["make ci-pr"],
        "pulumi-mutation.yml": ["make test-mutation"],
        "pulumi-policy.yml": ["make test-policy"],
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
        assert "pull_request" in triggers
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


def test_actions_are_pinned_to_full_commit_shas() -> None:
    """Keep GitHub Actions dependencies pinned to immutable refs."""
    for workflow_path in sorted(WORKFLOWS_DIR.glob("*.yml")):
        workflow = yaml.safe_load(workflow_path.read_text(encoding="utf-8"))

        for job in workflow.get("jobs", {}).values():
            uses = job.get("uses")
            if uses and not uses.startswith("./"):
                assert ACTION_SHA_REF.match(uses), (
                    f"{workflow_path.name} must pin reusable workflow `{uses}` "
                    "to a full commit SHA"
                )
            for step in job.get("steps", []):
                uses = step.get("uses")
                if not uses or uses.startswith("./"):
                    continue

                assert ACTION_SHA_REF.match(uses), (
                    f"{workflow_path.name} must pin `{uses}` to a full commit SHA"
                )


def test_template_sync_workflows_keep_guardrails() -> None:
    """Lock down template sync permissions, concurrency, and schedules."""
    app_workflow = yaml.safe_load(
        (WORKFLOWS_DIR / "template-sync-app.yml").read_text(encoding="utf-8")
    )
    pat_workflow = yaml.safe_load(
        (WORKFLOWS_DIR / "template-sync-pat.yml").read_text(encoding="utf-8")
    )

    for workflow_name in TEMPLATE_SYNC_WORKFLOWS:
        workflow = yaml.safe_load(
            (WORKFLOWS_DIR / workflow_name).read_text(encoding="utf-8")
        )
        assert "schedule" in _triggers(workflow)
        assert "workflow_dispatch" in _triggers(workflow)
        assert workflow["concurrency"]["cancel-in-progress"] is True
        assert workflow["jobs"]["repo-sync"]["timeout-minutes"] == 20

    assert app_workflow["jobs"]["repo-sync"]["permissions"] == {"contents": "read"}
    assert (
        _checkout_step(
            app_workflow["jobs"]["repo-sync"]["steps"],
            workflow_name="template-sync-app.yml",
        )["with"]["persist-credentials"]
        is False
    )
    assert pat_workflow["jobs"]["repo-sync"]["permissions"] == {
        "contents": "write",
        "pull-requests": "write",
    }
    assert (
        _checkout_step(
            pat_workflow["jobs"]["repo-sync"]["steps"],
            workflow_name="template-sync-pat.yml",
        )["with"]["persist-credentials"]
        is False
    )


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
    assert "env" not in jobs["ruff"]
    assert "env" not in jobs["ty"]

    ruff_runs = [step.get("run") for step in jobs.get("ruff", {}).get("steps", [])]
    ty_runs = [step.get("run") for step in jobs.get("ty", {}).get("steps", [])]

    assert triggers["push"]["branches"] == ["main"]
    assert "pull_request" in triggers
    assert any(run and "make test-ruff" in run for run in ruff_runs)
    assert any(run and "make test-ty" in run for run in ty_runs)


def test_policy_workflow_runs_on_push_and_pull_request() -> None:
    """Keep Pulumi policy validation wired into the PR check surface."""
    workflow = yaml.safe_load(
        (WORKFLOWS_DIR / "pulumi-policy.yml").read_text(encoding="utf-8")
    )
    triggers = _triggers(workflow)
    steps = workflow["jobs"]["policy"]["steps"]
    runs = [step.get("run") for step in steps if step.get("run")]

    assert triggers["push"]["branches"] == ["main"]
    assert "pull_request" in triggers
    assert any(run and "make test-policy" in run for run in runs)


def test_operator_docs_are_present_and_indexed() -> None:
    """Keep the root documentation discoverable from the handbook and README."""
    docs_index = DOCS_INDEX.read_text(encoding="utf-8")
    root_readme = ROOT_README.read_text(encoding="utf-8")

    for doc_name in DETAILED_DOCS:
        assert (PROJECT_ROOT / "docs" / doc_name).exists()
        assert doc_name in docs_index
        assert f"docs/{doc_name}" in root_readme

    assert "/home/dev/.venvs/infrastructure-template" not in docs_index
    assert "/home/dev/.venvs/infrastructure-template" not in root_readme
    assert "docker-compose.yml" in docs_index
    assert "docker-compose.yml" in root_readme


def test_testing_docs_call_out_full_coverage_contract() -> None:
    """Keep the operator docs explicit about mandatory 100% line coverage."""
    testing_doc = (PROJECT_ROOT / "docs" / "testing.md").read_text(encoding="utf-8")
    guardrails_doc = (PROJECT_ROOT / "docs" / "pulumi-guardrails.md").read_text(
        encoding="utf-8"
    )

    assert "100% line coverage" in testing_doc
    assert "100% line coverage" in guardrails_doc


def test_ci_architecture_docs_match_make_entrypoints() -> None:
    """Keep the CI architecture guide aligned with the current make targets."""
    architecture_doc = (PROJECT_ROOT / "docs" / "ci-architecture.md").read_text(
        encoding="utf-8"
    )

    assert "prerequisite sanity check" in architecture_doc
    assert "Pulumi structural tests" in architecture_doc
    assert "make ci-pr" in architecture_doc
