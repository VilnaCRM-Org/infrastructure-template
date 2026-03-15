"""Enable coverage collection in subprocesses when configured."""

try:
    import coverage
except ImportError:  # pragma: no cover - best-effort only
    coverage = None

if coverage is not None:
    coverage.process_startup()
