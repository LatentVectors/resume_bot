from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import jinja2
from loguru import logger
from pydantic import BaseModel, ConfigDict
from PyPDF2 import PdfReader
from weasyprint import CSS, HTML  # type: ignore


def get_template_environment(templates_dir: str | Path) -> jinja2.Environment:
    """
    Create and configure Jinja2 template environment.

    Args:
        templates_dir: Path to the templates directory

    Returns:
        Configured Jinja2 environment
    """
    templates_path = Path(templates_dir)
    if not templates_path.exists():
        raise FileNotFoundError(f"Templates directory not found: {templates_path}")

    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(templates_path)),
        autoescape=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )


def render_template_to_html(
    template_name: str, context: Dict[str, Any], templates_dir: str | Path
) -> str:
    """
    Render a Jinja2 template to HTML string.

    Args:
        template_name: Name of the template file (e.g., 'resume_001.html')
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
    except jinja2.TemplateNotFound:
        logger.error(f"Template not found: {template_name}", exception=True)
        raise
    except jinja2.TemplateError:
        logger.error(f"Template rendering failed: {template_name}", exception=True)
        raise


def convert_html_to_pdf(
    html_content: str, output_path: str | Path, css_string: Optional[str] = None
) -> Path:
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

        logger.debug(f"PDF generated successfully: {output_path}")
        return output_path

    except Exception:
        logger.error(f"Failed to generate PDF: {output_path}", exception=True)
        raise


def render_template_to_pdf(
    template_name: str,
    context: Dict[str, Any],
    output_path: str | Path,
    templates_dir: str | Path,
    css_string: Optional[str] = None,
) -> Path:
    """
    Render a Jinja2 template to PDF file.

    Args:
        template_name: Name of the template file (e.g., 'resume_001.html')
        context: Data context for template rendering
        output_path: Path where PDF should be saved
        templates_dir: Path to the templates directory
        css_string: Optional CSS string for additional styling

    Returns:
        Path to the created PDF file
    """
    # Render template to HTML
    html_content = render_template_to_html(template_name, context, templates_dir)

    # Convert HTML to PDF
    return convert_html_to_pdf(html_content, output_path, css_string)


class PageMetric(BaseModel):
    """Immutable per-page metrics for a PDF page.

    percent_filled is a value between 0.0 and 1.0 inclusive.
    """

    model_config = ConfigDict(frozen=True)

    page_number: int
    margin: float
    min_x: float
    max_x: float
    min_y: float
    max_y: float
    percent_filled: float


class PDFMetrics(BaseModel):
    """Immutable document-level metrics across all pages."""

    model_config = ConfigDict(frozen=True)

    total_pages: int
    page_metrics: List[PageMetric]


def compute_pdf_metrics(pdf_path: str | Path) -> PDFMetrics:
    """Compute per-page content extrema, uniform margin, and fill percentage metrics.

    Returns immutable Pydantic models capturing metrics for each page.
    """
    pdf_path = Path(pdf_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Analyze page extents using pdfminer.six layout
    extents = _analyze_pdf_page_extents(pdf_path)

    if not extents:
        return PDFMetrics(total_pages=0, page_metrics=[])

    margin = _compute_uniform_margin(extents)
    percentages = _compute_page_fill_percentages(extents, margin)

    page_metrics: list[PageMetric] = []
    for i, (ext, pct) in enumerate(zip(extents, percentages), start=1):
        page_metrics.append(
            PageMetric(
                page_number=i,
                margin=margin,
                min_x=ext["min_x"],
                max_x=ext["max_x"],
                min_y=ext["min_y"],
                max_y=ext["max_y"],
                percent_filled=pct,
            )
        )

    return PDFMetrics(total_pages=len(extents), page_metrics=page_metrics)


def compute_resume_page_length(percentages: list[float]) -> float:
    """Aggregate resume page length from per-page fill percentages.

    - If only one page: return its percent filled.
    - If multiple pages: (num_pages - 1) + last_page_percent.
    """
    if not percentages:
        return 0.0
    if len(percentages) == 1:
        return float(_clamp(percentages[0], 0.0, 1.0))
    return float(len(percentages) - 1 + _clamp(percentages[-1], 0.0, 1.0))


def _analyze_pdf_page_extents(pdf_path: Path) -> list[dict[str, float]]:
    """Return per-page content extents and page size using pdfminer.six.

    Each item: {min_x, max_x, min_y, max_y, page_width, page_height}
    If a page has no detectable content, min values will equal page dimension
    and max values will be 0.
    """
    # Lazy import to reduce CLI import overhead
    from pdfminer.high_level import extract_pages  # type: ignore
    from pdfminer.layout import LAParams  # type: ignore

    laparams = LAParams()
    extents: list[dict[str, float]] = []

    for page_layout in extract_pages(str(pdf_path), laparams=laparams):
        # pdfminer LTPage provides bbox as (x0, y0, x1, y1)
        try:
            x0, y0, x1, y1 = page_layout.bbox  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            # Fallbacks in case of version differences
            x0, y0 = 0.0, 0.0
            x1 = float(getattr(page_layout, "width", 0.0))
            y1 = float(getattr(page_layout, "height", 0.0))

        page_width = float(x1 - x0)
        page_height = float(y1 - y0)

        # Initialize extremes
        min_x = page_width
        max_x = 0.0
        min_y = page_height
        max_y = 0.0
        found_any = False

        for element in _iter_layout_elements(page_layout):
            bbox = getattr(element, "bbox", None)
            if not bbox or not isinstance(bbox, tuple) or len(bbox) != 4:
                continue
            ex0, ey0, ex1, ey1 = bbox
            # Skip zero-area or invalid boxes
            if ex1 <= ex0 or ey1 <= ey0:
                continue
            found_any = True
            if ex0 < min_x:
                min_x = float(ex0)
            if ex1 > max_x:
                max_x = float(ex1)
            if ey0 < min_y:
                min_y = float(ey0)
            if ey1 > max_y:
                max_y = float(ey1)

        if not found_any:
            # Keep defaults that indicate no content
            min_x = page_width
            min_y = page_height
            max_x = 0.0
            max_y = 0.0

        extents.append(
            {
                "min_x": float(min_x),
                "max_x": float(max_x),
                "min_y": float(min_y),
                "max_y": float(max_y),
                "page_width": float(page_width),
                "page_height": float(page_height),
            }
        )

    return extents


def _iter_layout_elements(layout_obj: object) -> Iterable[object]:
    """Depth-first iteration over pdfminer layout elements that have bbox."""
    # Many layout objects in pdfminer are iterable containers
    stack = [layout_obj]
    while stack:
        obj = stack.pop()
        # Skip the root LTPage from yielding; we only want its children
        try:
            children = list(obj)
        except Exception:  # noqa: BLE001
            children = []
        for child in children:
            # Yield child if it has a bbox; also continue descending into containers
            if hasattr(child, "bbox"):
                yield child
            # Descend further for compound elements (e.g., LTFigure, LTTextBox)
            try:
                if len(list(child)):
                    stack.append(child)
            except Exception:  # noqa: BLE001
                continue


def _compute_uniform_margin(extents: list[dict[str, float]]) -> float:
    """Infer a uniform margin as the minimum distance to edges across all pages."""
    margin = float("inf")
    for e in extents:
        left = max(0.0, e["min_x"] - 0.0)
        right = max(0.0, e["page_width"] - e["max_x"])
        bottom = max(0.0, e["min_y"] - 0.0)
        top = max(0.0, e["page_height"] - e["max_y"])
        margin = min(margin, left, right, top, bottom)

    if margin == float("inf"):
        return 0.0
    # Clamp to non-negative and not more than half of page height just in case
    # Use first page height as a bound if available
    page_height = extents[0]["page_height"] if extents else 0.0
    return _clamp(margin, 0.0, page_height / 2 if page_height > 0 else margin)


def _compute_page_fill_percentages(extents: list[dict[str, float]], margin: float) -> list[float]:
    """Compute vertical fill percentage for each page based on extents and uniform margin."""
    percentages: list[float] = []
    for e in extents:
        page_height = e["page_height"]
        # Guard against degenerate sizes
        usable_height = max(0.0, page_height - 2.0 * margin)
        if usable_height <= 0.0:
            percentages.append(1.0)
            continue
        # According to PDF coordinate system (origin bottom-left)
        vertical_extent = max(0.0, page_height - e["min_y"] - margin)
        pct = _clamp(vertical_extent / usable_height, 0.0, 1.0)
        percentages.append(float(pct))
    return percentages


def _clamp(value: float, min_value: float, max_value: float) -> float:
    return max(min_value, min(max_value, value))


def get_pdf_page_count(pdf_path: str | Path) -> int:
    """
    Get the number of pages in a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Number of pages in the PDF

    Raises:
        FileNotFoundError: If PDF file doesn't exist
        Exception: If PDF reading fails
    """
    try:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        with open(pdf_path, "rb") as file:
            reader = PdfReader(file)
            page_count = len(reader.pages)

        logger.debug(f"PDF page count: {page_count} pages in {pdf_path}")
        return page_count

    except Exception:
        logger.error(f"Failed to read PDF page count: {pdf_path}", exception=True)
        raise


def get_pdf_file_size(pdf_path: str | Path) -> int:
    """
    Get the file size of a PDF in bytes.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        File size in bytes

    Raises:
        FileNotFoundError: If PDF file doesn't exist
    """
    try:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        file_size = pdf_path.stat().st_size
        logger.debug(f"PDF file size: {file_size} bytes for {pdf_path}")
        return file_size

    except Exception:
        logger.error(f"Failed to get PDF file size: {pdf_path}", exception=True)
        raise


def get_pdf_info(pdf_path: str | Path) -> Dict[str, Any]:
    """
    Get comprehensive information about a PDF file.

    Args:
        pdf_path: Path to the PDF file

    Returns:
        Dictionary containing page count, file size, and other metadata
    """
    try:
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Get basic info
        page_count = get_pdf_page_count(pdf_path)
        file_size = get_pdf_file_size(pdf_path)

        # Get additional metadata
        with open(pdf_path, "rb") as file:
            reader = PdfReader(file)
            metadata = reader.metadata if reader.metadata else {}

        info = {
            "page_count": page_count,
            "file_size_bytes": file_size,
            "file_size_mb": round(file_size / (1024 * 1024), 2),
            "metadata": metadata,
            "path": str(pdf_path),
        }

        logger.debug(f"PDF info retrieved: {info}")
        return info

    except Exception:
        logger.error(f"Failed to get PDF info: {pdf_path}", exception=True)
        raise


def list_available_templates(templates_dir: str | Path) -> list[str]:
    """
    List all available HTML templates in the templates directory.

    Args:
        templates_dir: Path to the templates directory

    Returns:
        List of template filenames
    """
    try:
        templates_path = Path(templates_dir)
        if not templates_path.exists():
            raise FileNotFoundError(f"Templates directory not found: {templates_path}")

        templates = [
            f.name for f in templates_path.iterdir() if f.is_file() and f.suffix.lower() == ".html"
        ]

        logger.debug(f"Found {len(templates)} templates in {templates_path}")
        return sorted(templates)

    except Exception:
        logger.error(f"Failed to list templates: {templates_dir}", exception=True)
        raise
