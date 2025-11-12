import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PULUMI_PROGRAM_ROOT = PROJECT_ROOT / "pulumi"

if str(PULUMI_PROGRAM_ROOT) not in sys.path:
    sys.path.insert(0, str(PULUMI_PROGRAM_ROOT))
