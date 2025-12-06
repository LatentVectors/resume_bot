"""CLI interface for OpenRouter model operations."""

from __future__ import annotations

import typer
from rich.console import Console

# Create the models CLI app
models_app = typer.Typer(help="Manage OpenRouter models")

# Console for rich output
console = Console()


@models_app.command("sync")
def sync_models_command() -> None:
    """Sync available models from OpenRouter and generate enum."""
    console.print("Fetching models from OpenRouter...", style="cyan")

    # Import inside command to avoid expensive imports at CLI startup
    from .sync import fetch_models, generate_models_file

    try:
        models = fetch_models()
        console.print(f"[green]Fetched {len(models)} models[/green]")

        console.print("Generating ModelName enum...", style="cyan")
        count = generate_models_file(models)
        console.print(
            f"[bold green]Successfully generated ModelName enum with {count} models "
            f"at [bold]src/shared/model_names.py[/bold][/bold green]"
        )

    except ValueError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1) from e
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    models_app()
