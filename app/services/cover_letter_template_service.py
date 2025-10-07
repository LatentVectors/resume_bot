from __future__ import annotations

from jinja2 import Environment

from app.services.template_service import TemplateVersion
from src.config import settings
from src.features.cover_letter.content import DUMMY_COVER_LETTER_DATA
from src.features.cover_letter.llm_template import generate_cover_letter_template_html
from src.features.cover_letter.utils import convert_html_to_pdf
from src.features.cover_letter.validation import validate_template_minimal
from src.logging_config import logger


class CoverLetterTemplateService:
    """Coordinate cover letter template generation, validation, and PDF rendering."""

    @staticmethod
    def generate_version(
        user_text: str,
        image_file: bytes | None,
        current_html: str | None,
    ) -> TemplateVersion:
        """Generate a new cover letter template version and render a PDF preview.

        Args:
            user_text: The user's instruction or feedback for the template.
            image_file: Optional single image as raw bytes (PNG/JPEG/WebP accepted upstream).
            current_html: Currently selected template HTML if editing; None for first generation.

        Returns:
            TemplateVersion with fields: html, pdf_bytes, warnings.

        Raises:
            ValueError: If LLM returns empty HTML.
            RuntimeError: If template rendering fails.
        """
        # 1) Call LLM to produce raw HTML (no markdown fences)
        logger.info("Generating cover letter template HTML via LLM (current_html provided=%s)", bool(current_html))
        html_text: str = generate_cover_letter_template_html(
            user_text=user_text or "",
            current_html=current_html,
            image=image_file,
        )

        if not isinstance(html_text, str) or not html_text.strip():
            raise ValueError("Model returned empty cover letter template HTML")

        # 2) Validate minimal template contract
        is_valid, warnings = validate_template_minimal(html_text)
        if not is_valid:
            logger.warning("Cover letter template failed minimal validation; proceeding with warnings")

        # 3) Render HTML to PDF using dummy cover letter data
        # Note: Keep date as date object for Jinja2 strftime() support
        context = {
            "name": DUMMY_COVER_LETTER_DATA.name,
            "title": DUMMY_COVER_LETTER_DATA.title,
            "email": DUMMY_COVER_LETTER_DATA.email,
            "phone": DUMMY_COVER_LETTER_DATA.phone,
            "date": DUMMY_COVER_LETTER_DATA.date,  # datetime.date object
            "body_paragraphs": DUMMY_COVER_LETTER_DATA.body_paragraphs,
        }

        # Create temporary directory for preview rendering
        output_dir = (settings.data_dir / "tmp" / "cover_letter_template_previews").resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_pdf_path = output_dir / "preview.pdf"

        # Render: substitute context by simple Jinja2 rendering
        try:
            env = Environment(autoescape=True, trim_blocks=True, lstrip_blocks=True)
            template = env.from_string(html_text)
            rendered_html = template.render(**context)
            logger.debug(f"Rendered HTML length: {len(rendered_html)} chars")
        except Exception as e:
            logger.exception(e)
            # Propagate rendering failure after validation warnings are captured
            raise RuntimeError(f"Cover letter template rendering failed: {e}") from e

        try:
            logger.debug(f"Converting HTML to PDF at: {output_pdf_path}")
            convert_html_to_pdf(rendered_html, output_pdf_path)
            if not output_pdf_path.exists():
                raise RuntimeError("PDF file was not created")
            pdf_bytes = output_pdf_path.read_bytes()
            if not pdf_bytes:
                raise RuntimeError("PDF file is empty")
        except Exception as e:
            logger.exception("PDF conversion failed for cover letter template")
            raise RuntimeError(f"Failed to convert cover letter template to PDF: {e}") from e
        finally:
            # Best-effort cleanup
            try:
                output_pdf_path.unlink(missing_ok=True)  # type: ignore[arg-type]
            except Exception:  # noqa: BLE001
                pass

        return TemplateVersion(html=html_text, pdf_bytes=pdf_bytes, warnings=warnings)
