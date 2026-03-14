"""Enable coverage collection in subprocesses when configured."""

from typing import Any

coverage_module: Any | None

try:
    import coverage as coverage_module
except Exception:  # pragma: no cover - best-effort only
    coverage_module = None

if coverage_module is not None:
    coverage_module.process_startup()
