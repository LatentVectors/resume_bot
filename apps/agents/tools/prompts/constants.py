"""Constants for the prompts tools module."""

from __future__ import annotations

from pathlib import Path
from typing import Final

# Get the project root directory (tools/prompts/constants.py -> project root)
_PROJECT_ROOT = Path(__file__).parent.parent.parent

# Prompts directory at the root of the project
PROMPTS_DIR: Final[Path] = _PROJECT_ROOT / "prompts"

# Source directory for generated code
SRC_DIR: Final[Path] = _PROJECT_ROOT / "src"
