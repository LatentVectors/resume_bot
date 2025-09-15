"""Tab renderers for the Job detail page.

Exports individual functions to render each tab. These are imported by
`app/pages/job.py` and invoked conditionally based on the selected tab.
"""

from __future__ import annotations

from .cover import render_cover
from .messages import render_messages
from .notes import render_notes
from .overview import render_overview
from .responses import render_responses
from .resume import render_resume
from .utils import SupportsJob, badge, fmt_datetime, resume_exists

__all__ = [
    "render_overview",
    "render_resume",
    "render_cover",
    "render_responses",
    "render_messages",
    "render_notes",
    "SupportsJob",
    "badge",
    "resume_exists",
    "fmt_datetime",
]
