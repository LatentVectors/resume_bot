from __future__ import annotations

from pathlib import Path
from typing import Any

from loguru import logger
from weasyprint import CSS, HTML  # type: ignore

from src.features.resume.utils import get_template_environment


def list_available_templates(templates_dir: str | Path) -> list[str]:
    """
    List all available HTML templates in the cover letter templates directory.

    Args:
        templates_dir: Path to the templates directory

    Returns:
        List of template filenames, sorted alphabetically
    """
    try:
        templates_path = Path(templates_dir)
        if not templates_path.exists():
            raise FileNotFoundError(f"Templates directory not found: {templates_path}")

        templates = [f.name for f in templates_path.iterdir() if f.is_file() and f.suffix.lower() == ".html"]

        logger.debug(f"Found {len(templates)} cover letter templates in {templates_path}")
        return sorted(templates)

    except Exception:
        logger.error(f"Failed to list cover letter templates: {templates_dir}", exception=True)
        raise


def convert_html_to_pdf(html_content: str, output_path: str | Path, css_string: str | None = None) -> Path:
    """
    Convert HTML content to PDF file.

    Args:
        html_content: HTML string to convert
        output_path: Path where PDF should be saved
        css_string: Optional CSS string for additional styling

    Returns:
        Path to the created PDF file

    Raises:
        Exception: If PDF generation fails
    """
    try:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create HTML object
        html_doc = HTML(string=html_content)

        # Add CSS if provided
        css_docs = []
        if css_string:
            css_docs.append(CSS(string=css_string))

        # Generate PDF
        html_doc.write_pdf(str(output_path), stylesheets=css_docs)

        logger.debug(f"Cover letter PDF generated successfully: {output_path}")
        return output_path

    except Exception:
        logger.error(f"Failed to generate cover letter PDF: {output_path}", exception=True)
        raise


def render_template_to_html(template_name: str, context: dict[str, Any], templates_dir: str | Path) -> str:
    """
    Render a Jinja2 cover letter template to HTML string.

    Args:
        template_name: Name of the template file (e.g., 'cover_000.html')
        context: Data context for template rendering
        templates_dir: Path to the templates directory

    Returns:
        Rendered HTML string

    Raises:
        jinja2.TemplateNotFound: If template doesn't exist
        jinja2.TemplateError: If template rendering fails
    """
    try:
        env = get_template_environment(templates_dir)
        template = env.get_template(template_name)
        result: str = template.render(**context)
        return result
    except Exception:
        logger.error(f"Cover letter template rendering failed: {template_name}", exception=True)
        raise


def render_template_to_pdf_bytes(
    template_name: str,
    context: dict[str, Any],
    templates_dir: str | Path,
    css_string: str | None = None,
) -> bytes:
    """
    Render a Jinja2 cover letter template to a PDF and return the PDF as bytes.

    Args:
        template_name: Name of the template file (e.g., 'cover_000.html')
        context: Data context for template rendering
        templates_dir: Path to the templates directory
        css_string: Optional CSS string for additional styling

    Returns:
        PDF document as raw bytes

    Raises:
        Exception: If PDF generation fails
    """
    try:
        html_content = render_template_to_html(template_name, context, templates_dir)
        html_doc = HTML(string=html_content)

        css_docs = []
        if css_string:
            css_docs.append(CSS(string=css_string))

        pdf_bytes: bytes = html_doc.write_pdf(stylesheets=css_docs)
        logger.debug(f"Cover letter PDF bytes generated successfully: template={template_name}")
        return pdf_bytes

    except Exception:
        logger.error(
            f"Failed to generate cover letter PDF bytes for template: {template_name}",
            exception=True,
        )
        raise
