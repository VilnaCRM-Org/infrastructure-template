#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

from _script_support import (
    discover_stacks,
    ensure_empty_passphrase_for_file_backend,
    ensure_file_backend_directory,
    repo_root,
    run,
)


def main() -> int:
    root_dir = repo_root(__file__)
    pulumi_dir = Path(os.environ.get("PULUMI_DIR", root_dir / "pulumi"))
    policy_pack_dir = Path(os.environ.get("POLICY_PACK_DIR", root_dir / "policy"))
    preview_artifact_dir = Path(
        os.environ.get(
            "PREVIEW_ARTIFACT_DIR", root_dir / ".artifacts" / "pulumi-preview"
        )
    )
    summary_file = preview_artifact_dir / "summary.md"
    backend_url = os.environ.get(
        "PULUMI_BACKEND_URL",
        (root_dir / ".pulumi-backend").resolve().as_uri(),
    )

    preview_artifact_dir.mkdir(parents=True, exist_ok=True)
    for preview_file in preview_artifact_dir.glob("*.json"):
        preview_file.unlink()
    if summary_file.exists():
        summary_file.unlink()

    env = os.environ.copy()
    env.setdefault("PULUMI_BACKEND_URL", backend_url)
    env = ensure_empty_passphrase_for_file_backend(env)
    ensure_file_backend_directory(backend_url)
    run(
        [sys.executable, str(root_dir / "scripts" / "prepare_policy_pack.py")],
        cwd=root_dir,
        env=env,
    )

    stacks = discover_stacks(pulumi_dir, env.get("PULUMI_PREVIEW_STACKS"))
    if not stacks:
        print(
            f"error: no Pulumi stack configs found under {pulumi_dir}", file=sys.stderr
        )
        return 1

    run(
        ["pulumi", "--cwd", str(pulumi_dir), "login", "--non-interactive", backend_url],
        env=env,
    )

    for stack in stacks:
        safe_stack = "".join(
            character if character.isalnum() or character in "._-" else "_"
            for character in stack
        )
        preview_file = preview_artifact_dir / f"{safe_stack}.json"

        run(
            [
                "pulumi",
                "--cwd",
                str(pulumi_dir),
                "stack",
                "select",
                stack,
                "--create",
                "--non-interactive",
            ],
            env=env,
        )

        with preview_file.open("w", encoding="utf-8") as handle:
            run(
                [
                    "pulumi",
                    "--cwd",
                    str(pulumi_dir),
                    "preview",
                    "--stack",
                    stack,
                    "--non-interactive",
                    "--json",
                    "--policy-pack",
                    str(policy_pack_dir),
                ],
                env=env,
                stdout=handle,
            )

        summary = run(
            [
                "uv",
                "--project",
                str(root_dir),
                "run",
                "python",
                str(root_dir / "scripts" / "pulumi_ci_guardrails.py"),
                "summarize",
                str(preview_file),
            ],
            capture_output=True,
            env=env,
        )
        with summary_file.open("a", encoding="utf-8") as handle:
            handle.write(summary.stdout)

    print(summary_file.read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
