"""Service for template generation and validation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from src.config import settings
from src.features.resume.content import DUMMY_RESUME_DATA
from src.features.resume.llm_template import generate_template_html
from src.features.resume.utils import convert_html_to_pdf
from src.features.resume.validation import validate_template_minimal
from src.logging_config import logger


class TemplateVersion(BaseModel):
    """In-memory representation of a generated template version."""

    model_config = ConfigDict(frozen=True)

    html: str
    pdf_bytes: bytes
    warnings: list[str]


class TemplateService:
    """Coordinate template generation, validation, and PDF rendering."""

    @staticmethod
    def generate_version(
        user_text: str,
        image_file: bytes | None,
        current_html: str | None,
    ) -> TemplateVersion:
        """Generate a new template version and render a PDF preview.

        Args:
            user_text: The user's instruction or feedback for the template.
            image_file: Optional single image as raw bytes (PNG/JPEG/WebP accepted upstream).
            current_html: Currently selected template HTML if editing; None for first generation.

        Returns:
            TemplateVersion with fields: html, pdf_bytes, warnings.

        Raises:
            Exception: Propagates exceptions from LLM, validation, or rendering failures.
        """
        # 1) Call LLM to produce raw HTML (no markdown fences)
        logger.info("Generating template HTML via LLM (current_html provided=%s)", bool(current_html))
        html_text: str = generate_template_html(
            user_text=user_text or "",
            current_html=current_html,
            image=image_file,  # upstream supports bytes or URL/data URL; we pass bytes
        )

        if not isinstance(html_text, str) or not html_text.strip():
            raise ValueError("Model returned empty template HTML")

        # 2) Validate minimal template contract
        is_valid, warnings = validate_template_minimal(html_text)
        if not is_valid:
            logger.warning("Template failed minimal validation; proceeding with warnings")

        # 3) Render HTML to PDF using first dummy profile
        profile_keys = list(DUMMY_RESUME_DATA.keys())
        if not profile_keys:
            raise RuntimeError("No dummy profiles available for rendering")

        selected_key = profile_keys[0]
        profile = DUMMY_RESUME_DATA[selected_key]

        # Build simple Jinja2 context (match CLI structure)
        context = {
            "name": profile.name,
            "title": profile.title,
            "email": profile.email,
            "phone": profile.phone,
            "linkedin_url": profile.linkedin_url,
            "professional_summary": profile.professional_summary,
            "experience": [
                {
                    "title": exp.title,
                    "company": exp.company,
                    "location": exp.location,
                    "start_date": exp.start_date,
                    "end_date": exp.end_date,
                    "points": exp.points,
                }
                for exp in profile.experience
            ],
            "skills": profile.skills,
            "education": [
                {
                    "degree": edu.degree,
                    "major": edu.major,
                    "institution": edu.institution,
                    "grad_date": edu.grad_date,
                }
                for edu in profile.education
            ],
            "certifications": [{"title": cert.title, "date": cert.date} for cert in profile.certifications],
        }

        # To render arbitrary HTML (not a named file in templates dir), WeasyPrint can convert directly.
        # We use an ephemeral file path for output and then read its bytes, deleting afterwards.
        output_dir = (settings.data_dir / "tmp" / "template_previews").resolve()
        output_dir.mkdir(parents=True, exist_ok=True)
        output_pdf_path = output_dir / "preview.pdf"

        # Render: first substitute context by simple Jinja2 rendering using a StringTemplate env
        try:
            from jinja2 import Environment

            env = Environment(autoescape=True, trim_blocks=True, lstrip_blocks=True)
            template = env.from_string(html_text)
            rendered_html = template.render(**context)
        except Exception as e:  # noqa: BLE001
            logger.exception(e)
            # Propagate rendering failure after validation warnings are captured
            raise RuntimeError(f"Template rendering failed: {e}") from e

        try:
            convert_html_to_pdf(rendered_html, output_pdf_path)
            pdf_bytes = output_pdf_path.read_bytes()
        finally:
            # Best-effort cleanup
            try:
                output_pdf_path.unlink(missing_ok=True)  # type: ignore[arg-type]
            except Exception:  # noqa: BLE001
                pass

        return TemplateVersion(html=html_text, pdf_bytes=pdf_bytes, warnings=warnings)

