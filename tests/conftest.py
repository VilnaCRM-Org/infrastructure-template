"""Shared pytest setup for Pulumi tests."""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PULUMI_DIR = PROJECT_ROOT / "pulumi"

if str(PULUMI_DIR) not in sys.path:
    sys.path.insert(0, str(PULUMI_DIR))
