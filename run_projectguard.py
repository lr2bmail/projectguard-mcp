"""Repository-local launcher for ProjectGuard MCP.

This file lets users run ProjectGuard from a cloned repo even before the
editable package console script is available on PATH. It adds ./src to
sys.path, then runs projectguard_mcp.server:main.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from projectguard_mcp.server import main


if __name__ == "__main__":
    main()
