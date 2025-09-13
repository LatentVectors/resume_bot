from __future__ import annotations

import typer

from .types import ResumeData

app = typer.Typer(help="Resume management commands")


@app.command()
def generate() -> None:
    """Generate PDF samples for all resume templates using dummy data."""
    from pathlib import Path

    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.table import Table

    from src.config import DATA_DIR

    from .content import DUMMY_RESUME_DATA
    from .utils import get_pdf_info, list_available_templates, render_template_to_pdf

    console = Console()

    # Define templates directory and output directory
    templates_dir = Path("src/features/resume/templates")
    samples_dir = DATA_DIR / "samples" / "resumes"
    samples_dir.mkdir(parents=True, exist_ok=True)

    # Get available templates
    try:
        templates = list_available_templates(templates_dir)
        console.print(f"[green]Found {len(templates)} templates[/green]")
    except Exception as e:
        console.print(f"[red]Error listing templates: {e}[/red]")
        return

    # Create a table to display results
    table = Table(title="Resume Sample Generation Results")
    table.add_column("Template", style="cyan")
    table.add_column("Profile", style="magenta")
    table.add_column("Pages", style="green")
    table.add_column("Size (MB)", style="yellow")
    table.add_column("Status", style="bold")

    # Generate samples for each template with different profiles
    profile_names = list(DUMMY_RESUME_DATA.keys())

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Generating resume samples...", total=len(templates))

        for i, template_name in enumerate(templates):
            # Update progress description to show current template
            progress.update(task, description=f"Processing {template_name}...")

            # Use different profile for each template (cycling through profiles)
            profile_name = profile_names[i % len(profile_names)]
            profile_data = DUMMY_RESUME_DATA[profile_name]

            # Convert ResumeData to dict for template rendering
            context = {
                "name": profile_data.name,
                "title": profile_data.title,
                "email": profile_data.email,
                "phone": profile_data.phone,
                "linkedin_url": profile_data.linkedin_url,
                "professional_summary": profile_data.professional_summary,
                "experience": [
                    {
                        "title": exp.title,
                        "company": exp.company,
                        "location": exp.location,
                        "start_date": exp.start_date,
                        "end_date": exp.end_date,
                        "points": exp.points,
                    }
                    for exp in profile_data.experience
                ],
                "skills": profile_data.skills,
                "education": [
                    {
                        "degree": edu.degree,
                        "major": edu.major,
                        "institution": edu.institution,
                        "grad_date": edu.grad_date,
                    }
                    for edu in profile_data.education
                ],
                "certifications": [
                    {
                        "title": cert.title,
                        "date": cert.date,
                    }
                    for cert in profile_data.certifications
                ],
            }

            # Generate filename
            template_base = template_name.replace(".html", "")
            output_filename = f"{template_base}_{profile_name}.pdf"
            output_path = samples_dir / output_filename

            try:
                # Generate PDF
                pdf_path = render_template_to_pdf(
                    template_name, context, output_path, templates_dir
                )

                # Get PDF info
                info = get_pdf_info(pdf_path)

                # Add to table
                table.add_row(
                    template_name,
                    profile_name.replace("_", " ").title(),
                    str(info["page_count"]),
                    f"{info['file_size_mb']:.2f}",
                    "✅ Generated",
                )

            except Exception as e:
                table.add_row(
                    template_name,
                    profile_name.replace("_", " ").title(),
                    "-",
                    "-",
                    f"❌ Error: {str(e)[:50]}...",
                )

            progress.advance(task)

    # Display results
    console.print("\n")
    console.print(table)
    console.print(f"\n[green]Samples saved to: {samples_dir}[/green]")

    # List generated files
    generated_files = list(samples_dir.glob("*.pdf"))
    if generated_files:
        console.print(f"\n[blue]Generated {len(generated_files)} sample files:[/blue]")
        for file in sorted(generated_files):
            console.print(f"  • {file.name}")


@app.command()
def new_template(
    description: str | None = typer.Argument(
        None,
        help="Natural-language description of the desired resume template style/layout.",
    ),
    image: str | None = typer.Option(
        None,
        "--image",
        help="Local path or URL to a reference image to inform layout/style.",
    ),
    name: str | None = typer.Option(
        None,
        "--name",
        help="Template slug (default autogenerated, e.g., template_YYYYMMDD_HHMM).",
    ),
    outdir: str = typer.Option(
        "data/templates/generated",
        "--outdir",
        help="Base output directory for generated templates.",
    ),
    pdf: bool = typer.Option(
        False, "--pdf/--no-pdf", help="Also save a PDF preview alongside the HTML."
    ),
) -> None:
    """Generate a new ATS-safe Jinja2 HTML resume template via LLM, render, and save."""
    from datetime import datetime
    from pathlib import Path

    from langchain_core.messages import HumanMessage, SystemMessage
    from rich.console import Console

    console = Console()

    # Lazy imports to keep CLI startup lean
    from src.core.models import OpenAIModels, get_model

    from .content import DUMMY_RESUME_DATA
    from .prompt import resume_template_prompt
    from .utils import convert_html_to_pdf, render_template_to_html

    # Use default model per spec (gpt-4o)
    llm = get_model(OpenAIModels.gpt_4o)

    # Assemble multimodal user message
    user_text = (
        description or "Generate a clean, ATS-safe single-column resume template per system rules."
    ) + "\n\nOutput ONLY the final HTML for the Jinja2 template."
    content_parts = [{"type": "text", "text": user_text}]
    image_parts, warn = _prepare_image_content(image)
    content_parts.extend(image_parts)
    for w in warn:
        console.print(f"[yellow]{w}[/yellow]")

    # Invoke LLM
    resp = llm.invoke(
        [
            SystemMessage(content=resume_template_prompt),
            HumanMessage(content=content_parts),
        ]
    )

    # Extract text content
    html_text: str
    content = getattr(resp, "content", resp)  # type: ignore[assignment]
    if isinstance(content, list):
        # Concatenate any text parts
        html_text = "".join(part.get("text", "") for part in content if isinstance(part, dict))
    else:
        html_text = str(content)

    # Validate minimal template requirements
    is_ok, warnings = _validate_template_minimal(html_text)
    for w in warnings:
        console.print(f"[yellow]{w}[/yellow]")

    # Prepare output paths
    date_str = _today_str()
    slug = _slugify_name(name) if name else f"template_{datetime.now().strftime('%Y%m%d_%H%M')}"
    base_dir = Path(outdir) / date_str / slug
    base_dir.mkdir(parents=True, exist_ok=True)

    template_filename = f"{slug}.html"
    template_path = base_dir / template_filename
    pdf_path = base_dir / f"{slug}__preview.pdf"

    # Save raw template
    template_path.write_text(html_text, encoding="utf-8")

    # Build context from dummy profile
    profile_keys = list(DUMMY_RESUME_DATA.keys())
    if not profile_keys:
        console.print("[red]No dummy profiles available to render. Skipping render step.[/red]")
        context = {}
    else:
        selected_key = profile_keys[0]
        context = _build_context_from_profile(DUMMY_RESUME_DATA[selected_key])

    # Render template to HTML in-memory using the output directory as templates path
    rendered_html: str | None = None
    try:
        rendered_html = render_template_to_html(template_filename, context, base_dir)
    except Exception as e:  # noqa: BLE001
        console.print(f"[red]Rendering failed: {e}[/red]")

    # Optionally, generate PDF
    if pdf:
        try:
            # Prefer the already-rendered HTML; if missing, render again
            html_for_pdf = (
                rendered_html
                if rendered_html is not None
                else render_template_to_html(template_filename, context, base_dir)
            )
            convert_html_to_pdf(html_for_pdf, pdf_path)
        except Exception as e:  # noqa: BLE001
            console.print(f"[red]PDF generation failed: {e}[/red]")

    console.print("\n[green]Template generation complete.[/green]")
    console.print(f"Raw template: {template_path}")
    if pdf and pdf_path.exists():
        console.print(f"PDF preview: {pdf_path}")
    console.print(
        "\nNext steps: Review outputs and copy approved template into `src/features/resume/templates/`."
    )


def _build_context_from_profile(profile_data: ResumeData) -> dict:
    return {
        "name": profile_data.name,
        "title": profile_data.title,
        "email": profile_data.email,
        "phone": profile_data.phone,
        "linkedin_url": profile_data.linkedin_url,
        "professional_summary": profile_data.professional_summary,
        "experience": [
            {
                "title": exp.title,
                "company": exp.company,
                "location": exp.location,
                "start_date": exp.start_date,
                "end_date": exp.end_date,
                "points": exp.points,
            }
            for exp in profile_data.experience
        ],
        "skills": profile_data.skills,
        "education": [
            {
                "degree": edu.degree,
                "major": edu.major,
                "institution": edu.institution,
                "grad_date": edu.grad_date,
            }
            for edu in profile_data.education
        ],
        "certifications": [
            {"title": cert.title, "date": cert.date} for cert in profile_data.certifications
        ],
    }


def _slugify_name(name_text: str) -> str:
    import re

    slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", name_text.strip().lower())
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "template"


def _today_str() -> str:
    from datetime import datetime

    return datetime.now().strftime("%Y%m%d")


def _prepare_image_content(image: str | None) -> tuple[list[dict], list[str]]:
    """Return multimodal content parts for a HumanMessage and warnings.

    If image is a local file, embed as base64 data URL. If it's an http(s) URL, attach as image_url.
    If invalid path, return no image and a warning.
    """
    warnings: list[str] = []
    content_parts: list[dict] = []
    if not image:
        return content_parts, warnings

    import base64
    import mimetypes
    from pathlib import Path

    if image.startswith("http://") or image.startswith("https://"):
        content_parts.append({"type": "image_url", "image_url": image})
        return content_parts, warnings

    path = Path(image)
    if not path.exists():
        warnings.append(f"Image path not found: {path}. Proceeding without image.")
        return content_parts, warnings

    mime, _ = mimetypes.guess_type(str(path))
    mime = mime or "image/png"
    try:
        data = path.read_bytes()
        b64 = base64.b64encode(data).decode("utf-8")
        data_url = f"data:{mime};base64,{b64}"
        content_parts.append({"type": "image_url", "image_url": data_url})
    except Exception as e:  # noqa: BLE001
        warnings.append(f"Failed to read/encode image: {e}. Proceeding without image.")
    return content_parts, warnings


def _validate_template_minimal(html_text: str) -> tuple[bool, list[str]]:
    """Basic checks per contract; returns (is_valid, warnings)."""
    warnings: list[str] = []
    ok = True
    required = ["{{ name }}", "{{ title }}"]
    if not all(x in html_text for x in required):
        ok = False
        warnings.append("Missing one or more required placeholders: {{ name }}, {{ title }}")
    # Heuristic for at least one list section placeholder
    if not any(
        token in html_text for token in ["skills", "experience", "education", "certifications"]
    ):
        ok = False
        warnings.append(
            "Template seems to lack list sections (skills/experience/education/certifications)."
        )
    # Encourage if-wrapping but don't fail hard
    if "{% if" not in html_text:
        warnings.append(
            "No conditional sections detected. Ensure optional sections are wrapped in {% if ... %} blocks."
        )
    return ok, warnings
