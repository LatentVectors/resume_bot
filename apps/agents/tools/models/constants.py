"""Constants for the models tools module."""

from __future__ import annotations

from pathlib import Path
from typing import Final

# Get the project root directory (tools/models/constants.py -> project root)
_PROJECT_ROOT = Path(__file__).parent.parent.parent

# Source directory for generated code
SRC_DIR: Final[Path] = _PROJECT_ROOT / "src"

# OpenRouter API URL
OPENROUTER_API_URL: Final[str] = "https://openrouter.ai/api/v1/models"
