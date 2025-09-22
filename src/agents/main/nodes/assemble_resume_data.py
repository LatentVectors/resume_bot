"""Assemble the final ResumeData object for downstream consumers.

This node is a pure data assembly step. It performs NO file I/O and is intended
to replace the previous create_resume node that rendered a PDF. Rendering and
persistence are handled outside the agent graph by services.
"""

from __future__ import annotations

from src.features.resume.types import ResumeData, ResumeEducation, ResumeExperience
from src.logging_config import logger

from ..state import Experience, InternalState, PartialInternalState


def assemble_resume_data(state: InternalState) -> PartialInternalState:
    """Assemble a ResumeData object from the current InternalState.

    Reads the generated fields (title, professional_summary, skills, experiences)
    and user identity/education from the state and constructs a ResumeData model.

    This node intentionally does not persist or render anything. The assembled
    object will be returned by the graph in a subsequent section when the graph
    output/state is updated to include `resume_data`.

    Args:
        state: The current internal state of the agent

    Returns:
        PartialInternalState: Returns `resume_data` so the graph output can
        expose it via OutputState.
    """
    logger.debug("NODE: assemble_resume_data")

    # Transform experiences
    resume_experiences: list[ResumeExperience] = []
    for exp in state.experiences or []:
        assert isinstance(exp, Experience)
        resume_experiences.append(
            ResumeExperience(
                title=exp.title,
                company=exp.company,
                location="",
                start_date=exp.start_date,
                end_date=exp.end_date,
                points=list(exp.points or []),
            )
        )

    # Transform education
    resume_education: list[ResumeEducation] = []
    if state.user_education:
        for edu in state.user_education:
            resume_education.append(
                ResumeEducation(
                    degree=str(edu.get("degree", "")),
                    major="",
                    institution=str(edu.get("school", "")),
                    grad_date=edu.get("end_date", None),
                )
            )

    # Assemble the ResumeData object
    _resume_data = ResumeData(
        name=state.user_name or "",
        title=state.title or "",
        email=state.user_email or "",
        phone=state.user_phone or "",
        linkedin_url=state.user_linkedin_url or "",
        professional_summary=state.professional_summary or "",
        experience=resume_experiences,
        education=resume_education,
        skills=list(state.skills or []),
        certifications=[],
    )

    return PartialInternalState(resume_data=_resume_data)
