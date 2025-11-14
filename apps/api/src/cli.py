"""Root CLI aggregator for the resume bot."""

from __future__ import annotations

import typer

from src.core.models_cli import models_app
from src.core.prompts.cli import prompts_app

# Define the root-level app
app = typer.Typer(help="Resume Bot CLI - Manage resumes, jobs, and LangSmith operations")

# Attach sub-command groups
app.add_typer(prompts_app, name="prompts")
app.add_typer(models_app, name="models")

if __name__ == "__main__":
    app()
