"""Integration tests for Pulumi policy-pack execution."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
POLICY_DIR = PROJECT_ROOT / "policy"
PREPARE_POLICY_PACK = PROJECT_ROOT / "scripts" / "prepare_policy_pack.sh"

pytestmark = pytest.mark.skipif(
    subprocess.run(
        ["bash", "-lc", "command -v pulumi >/dev/null 2>&1"],
        check=False,
        cwd=PROJECT_ROOT,
        timeout=10,
    ).returncode
    != 0,
    reason="Pulumi CLI binary is not available in PATH.",
)


def _write_program(tmp_path: Path, *, acl: str) -> Path:
    """Create a small Pulumi program that exercises the S3 ACL guardrail."""
    work_dir = tmp_path / f"policy-{acl.replace('-', '_')}"
    work_dir.mkdir()
    (work_dir / ".state").mkdir()
    (work_dir / "Pulumi.yaml").write_text(
        "name: policy-pack-integration\nruntime:\n  name: python\n",
        encoding="utf-8",
    )
    (work_dir / "__main__.py").write_text(
        f"""import pulumi


class BucketStub(pulumi.ComponentResource):
    def __init__(self, name: str) -> None:
        super().__init__(
            "tests:s3/bucket:Bucket",
            name,
            {{
                "acl": "{acl}",
                "tags": {{"Project": "demo", "Environment": "dev"}},
            }},
        )
        self.register_outputs({{}})


BucketStub("bucket")
""",
        encoding="utf-8",
    )
    return work_dir


def _preview_with_policy_pack(work_dir: Path) -> subprocess.CompletedProcess[str]:
    """Run a local Pulumi preview with the repository policy pack enabled."""
    env = {
        **os.environ,
        "PULUMI_BACKEND_URL": f"file://{work_dir / '.state'}",
        "PULUMI_CONFIG_PASSPHRASE": "integration-test-passphrase",
    }

    subprocess.run(
        ["bash", str(PREPARE_POLICY_PACK)],
        check=True,
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
    )
    subprocess.run(
        ["pulumi", "--cwd", str(work_dir), "stack", "init", "dev"],
        check=True,
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
    )

    return subprocess.run(
        [
            "pulumi",
            "--cwd",
            str(work_dir),
            "preview",
            "--stack",
            "dev",
            "--non-interactive",
            "--policy-pack",
            str(POLICY_DIR),
        ],
        check=False,
        cwd=PROJECT_ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=120,
    )


def test_policy_pack_allows_private_bucket_acl(tmp_path: Path) -> None:
    """Keep the happy path green for compliant resource definitions."""
    result = _preview_with_policy_pack(_write_program(tmp_path, acl="private"))

    assert result.returncode == 0, result.stderr


def test_policy_pack_blocks_public_bucket_acl(tmp_path: Path) -> None:
    """Reject public-read ACLs during a real Pulumi preview."""
    result = _preview_with_policy_pack(_write_program(tmp_path, acl="public-read"))
    combined_output = f"{result.stdout}\n{result.stderr}"

    assert result.returncode != 0, combined_output
    assert "s3-no-public-acls" in combined_output
    assert "public-read or public-read-write ACLs" in combined_output
