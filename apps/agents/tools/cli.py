"""Root CLI for development tools.

This CLI provides development-only tools for managing the agents package.
These tools are not intended to be deployed with the production package.

Usage:
    python -m tools prompts sync      # Sync prompts from LangSmith
    python -m tools prompts generate  # Generate types from existing JSON files
    python -m tools models sync       # Sync models from OpenRouter
"""

from __future__ import annotations

from pathlib import Path

import typer
from dotenv import load_dotenv

from .models import models_app
from .prompts import prompts_app

# Load .env file from the project root (tools/cli.py -> project root)
_PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(_PROJECT_ROOT / ".env")

# Define the root-level app
app = typer.Typer(help="Development tools for the agents package")

# Attach sub-command groups
app.add_typer(prompts_app, name="prompts")
app.add_typer(models_app, name="models")

if __name__ == "__main__":
    app()
