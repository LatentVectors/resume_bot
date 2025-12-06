"""CLI interface for prompt operations."""

from __future__ import annotations

import typer
from rich.console import Console

# Create the prompts CLI app
prompts_app = typer.Typer(help="Manage prompts from LangSmith")

# Console for rich output
console = Console()


@prompts_app.command("sync")
def sync_prompts_command(
    fail_fast: bool = typer.Option(
        True,
        "--fail-fast/--no-fail-fast",
        help="Exit immediately on first error (default: True)",
    ),
) -> None:
    """Sync prompts from LangSmith to local storage and generate types."""
    console.print("Connecting to LangSmith...", style="cyan")

    # Import inside command to avoid expensive imports at CLI startup
    from .generators import generate_get_prompt, generate_prompt_enum, generate_prompt_input_types
    from .sync import sync_prompts_from_langsmith

    try:
        # Call business logic
        synced_count, errors = sync_prompts_from_langsmith()

        if not errors:
            console.print("Syncing prompts to /prompts/...", style="cyan")
            console.print(f"[bold green]Successfully synced {synced_count} prompts[/bold green]")

            # Generate enum
            console.print("Generating PromptName enum...", style="cyan")
            enum_count = generate_prompt_enum()
            console.print(
                f"Generated enum with {enum_count} prompts at [bold]src/shared/prompt_names.py[/bold]",
                style="green",
            )

            # Generate input types
            console.print("Generating prompt input types...", style="cyan")
            types_count = generate_prompt_input_types()
            console.print(
                f"Generated {types_count} input type classes at [bold]src/shared/prompt_types.py[/bold]",
                style="green",
            )

            # Generate get_prompt function
            console.print("Generating get_prompt() function...", style="cyan")
            get_prompt_count = generate_get_prompt()
            console.print(
                f"Generated get_prompt() with {get_prompt_count} overloads at [bold]src/shared/get_prompt.py[/bold]",
                style="green",
            )
        else:
            # Handle errors based on fail_fast
            if fail_fast and errors:
                prompt_name, error = errors[0]
                console.print(f"[bold red]Error:[/bold red] Failed to sync prompt '{prompt_name}': {error}")
                raise typer.Exit(1)
            else:
                console.print(
                    f"[yellow]Synced {synced_count}/{synced_count + len(errors)} prompts ({len(errors)} failed)[/yellow]"
                )
                console.print("\n[bold]Failed prompts:[/bold]")
                for prompt_name, error in errors:
                    console.print(f"  - {prompt_name}: {error}", style="red")
                raise typer.Exit(1)

    except (ValueError, RuntimeError) as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1) from e


@prompts_app.command("generate")
def generate_types_command() -> None:
    """Generate types from existing prompt JSON files (without syncing from LangSmith)."""
    console.print("Generating types from existing prompt files...", style="cyan")

    # Import inside command to avoid expensive imports at CLI startup
    from .generators import generate_get_prompt, generate_prompt_enum, generate_prompt_input_types

    try:
        # Generate enum
        console.print("Generating PromptName enum...", style="cyan")
        enum_count = generate_prompt_enum()
        console.print(
            f"Generated enum with {enum_count} prompts at [bold]src/shared/prompt_names.py[/bold]",
            style="green",
        )

        # Generate input types
        console.print("Generating prompt input types...", style="cyan")
        types_count = generate_prompt_input_types()
        console.print(
            f"Generated {types_count} input type classes at [bold]src/shared/prompt_types.py[/bold]",
            style="green",
        )

        # Generate get_prompt function
        console.print("Generating get_prompt() function...", style="cyan")
        get_prompt_count = generate_get_prompt()
        console.print(
            f"Generated get_prompt() with {get_prompt_count} overloads at [bold]src/shared/get_prompt.py[/bold]",
            style="green",
        )

        console.print("[bold green]Type generation complete![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    prompts_app()
