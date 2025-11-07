"""Constants for the prompts module."""

from __future__ import annotations

from pathlib import Path
from typing import Final

# Get the project root directory (4 levels up from this file)
_PROJECT_ROOT = Path(__file__).parent.parent.parent.parent

# Prompts directory at the root of the project
PROMPTS_DIR: Final[Path] = _PROJECT_ROOT / "prompts"

