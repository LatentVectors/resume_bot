"""Root CLI aggregator for the resume bot."""

from __future__ import annotations

import typer

from src.core.prompts.cli import prompts_app

# Define the root-level app
app = typer.Typer(help="Resume Bot CLI - Manage resumes, jobs, and LangSmith operations")

# Attach sub-command groups
app.add_typer(prompts_app, name="prompts")

if __name__ == "__main__":
    app()
