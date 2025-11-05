"""Resume refinement workflow for Step 3 of job intake.

Handles AI-assisted resume editing with tool-based update proposals.
"""

from __future__ import annotations

from typing import Annotated

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from pydantic import BaseModel, Field

from app.constants import LLMTag
from app.services.certificate_service import CertificateService
from app.services.education_service import EducationService
from app.services.experience_service import ExperienceService
from app.services.resume_service import ResumeService
from src.core.models import OpenAIModels, get_model
from src.features.resume.types import (
    ResumeCertification,
    ResumeData,
    ResumeEducation,
    ResumeExperience,
)
from src.logging_config import logger

# ==================== Main Workflow Function ====================


def run_resume_chat(
    messages: list,
    job,
    selected_version,
    gap_analysis: str,
    stakeholder_analysis: str,
    work_experience: str,
) -> tuple[AIMessage, int | None]:
    """Get AI response for resume refinement conversation.

    Args:
        messages: Chat history.
        job: Job object.
        selected_version: Selected resume version.
        gap_analysis: Gap analysis markdown from job intake (analyzes fit between job and experience).
        stakeholder_analysis: Stakeholder analysis markdown from job intake (analyzes hiring stakeholders).
        work_experience: Formatted work experience context for AI reference.

    Returns:
        Tuple of (AIMessage response, new_version_id if tool was used, else None).
    """
    # Parse current resume data for context
    resume_data = ResumeData.model_validate_json(selected_version.resume_json)
    current_resume_text = str(resume_data)

    # Build messages
    llm_messages = []
    for msg in messages:
        if isinstance(msg, HumanMessage):
            llm_messages.append({"role": "user", "content": msg.content})
        elif isinstance(msg, AIMessage):
            msg_dict = {"role": "assistant", "content": msg.content}
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                msg_dict["tool_calls"] = msg.tool_calls
            llm_messages.append(msg_dict)
        elif isinstance(msg, ToolMessage):
            llm_messages.append(
                {
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": msg.tool_call_id,
                }
            )

    # Create version tracker to capture version_id from tool execution
    version_tracker: dict[str, int | None] = {"version_id": None}

    # Prepare configuration with injected tool arguments
    config = RunnableConfig(
        tags=[LLMTag.INTAKE_RESUME_CHAT.value],
        configurable={
            "job_id": job.id,
            "user_id": job.user_id,
            "template_name": selected_version.template_name,
            "parent_version_id": selected_version.id,
            "version_tracker": version_tracker,
        },
    )

    try:
        response = _chain.invoke(
            {
                "message_history": llm_messages,
                "job_description": job.job_description,
                "current_resume": current_resume_text,
                "gap_analysis": gap_analysis,
                "stakeholder_analysis": stakeholder_analysis,
                "work_experience": work_experience,
            },
            config=config,
        )

        # Extract version_id from tracker (populated by tool if it was called)
        new_version_id = version_tracker.get("version_id")

        return response, new_version_id

    except Exception as exc:
        logger.exception("Error getting AI response: %s", exc)
        return AIMessage(content="I apologize, but I encountered an error. Please try again."), None


# ==================== System Prompt ====================

SYSTEM_PROMPT_TEMPLATE = """
You are an expert resume writer helping refine a resume for a job application.

Current job description:
{job_description}

Current resume:
{current_resume}

Gap Analysis:
{gap_analysis}

Stakeholder Analysis:
{stakeholder_analysis}

Work Experience Context:
{work_experience}

Your role:
- Review the current resume and propose specific improvements
- Use the propose_resume_draft tool to create new versions
- Each tool call must include COMPLETE resume content:
  * Professional title
  * Professional summary tailored to the job
  * All relevant skills
  * ALL experiences with their database IDs, refined titles, and compelling bullet points
  * Education IDs to include (reference the current resume for available education)
  * Certification IDs to include (reference the current resume for available certifications)
- Focus on tailoring content to match the job requirements
- Be specific and actionable in your suggestions

Important notes:
- When you use propose_resume_draft, you're creating a complete new draft, not making incremental updates
- You must provide the complete list of experiences every time, not just the ones you're changing
- The system will automatically preserve candidate information (name, email, phone, LinkedIn)
- For experiences, you provide the experience_id, refined job title, and bullet points
- The system will pull company name, location, and employment dates from the database
- Always include all education and certification IDs from the current resume unless you have a reason to exclude them
"""

# ==================== Pydantic Models for Tool Schema ====================


class ProposedExperience(BaseModel):
    """Experience entry for AI-proposed resume draft.

    AI provides the experience ID (from database) along with refined title and bullet points.
    Company, location, and dates are pulled from the database automatically.
    """

    experience_id: int = Field(description="Database ID of the experience record")
    title: str = Field(description="Job title (can be refined from original)")
    points: list[str] = Field(description="List of bullet points describing achievements and responsibilities")


# ==================== Tool Definitions ====================


@tool(response_format="content_and_artifact")
def propose_resume_draft(
    title: Annotated[str, "Professional title/headline for the resume"],
    professional_summary: Annotated[str, "Professional summary tailored to the job"],
    skills: Annotated[list[str], "List of skills relevant to the position"],
    experiences: Annotated[list[ProposedExperience], "Complete list of experiences to include in resume"],
    education_ids: Annotated[list[int], "List of education record IDs to include in resume"],
    certification_ids: Annotated[list[int], "List of certification record IDs to include in resume"],
    job_id: Annotated[int, InjectedToolArg],
    user_id: Annotated[int, InjectedToolArg],
    template_name: Annotated[str, InjectedToolArg],
    parent_version_id: Annotated[int | None, InjectedToolArg],
    version_tracker: Annotated[dict[str, int | None], InjectedToolArg],
) -> tuple[str, int]:
    """Propose a complete resume draft.

    Creates a new resume version with the proposed content. Each call must include
    complete resume data (title, summary, skills, all experiences with bullet points).

    Args:
        title: Professional title/headline
        professional_summary: Professional summary
        skills: List of skills
        experiences: Complete experience list with IDs, titles, and bullet points
        education_ids: Education record IDs to include
        certification_ids: Certification record IDs to include
        job_id: Job ID (injected)
        user_id: User ID (injected)
        template_name: Resume template name (injected)
        parent_version_id: Parent version ID (injected)
        version_tracker: Mutable dict to track created version_id (injected)

    Returns:
        Tuple of (confirmation message for AI, version_id as artifact)
    """
    try:
        # Get user data from database
        from src.database import db_manager

        user = db_manager.get_user(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        # Build experience list by fetching from database
        resume_experiences: list[ResumeExperience] = []
        for exp_proposal in experiences:
            # Fetch experience from database
            exp_record = ExperienceService.get_experience(exp_proposal.experience_id)
            if not exp_record:
                logger.warning(f"Experience {exp_proposal.experience_id} not found, skipping")
                continue

            # Create ResumeExperience with DB data + AI-generated content
            resume_experiences.append(
                ResumeExperience(
                    title=exp_proposal.title,
                    company=exp_record.company_name,
                    location=exp_record.location or "",
                    start_date=exp_record.start_date,
                    end_date=exp_record.end_date,
                    points=exp_proposal.points,
                )
            )

        # Build education list by fetching from database
        resume_education: list[ResumeEducation] = []
        for edu_id in education_ids:
            edu_record = EducationService.get_education(edu_id)
            if not edu_record:
                logger.warning(f"Education {edu_id} not found, skipping")
                continue

            resume_education.append(
                ResumeEducation(
                    degree=edu_record.degree,
                    major=edu_record.major,
                    institution=edu_record.institution,
                    grad_date=edu_record.grad_date,
                )
            )

        # Build certification list by fetching from database
        resume_certifications: list[ResumeCertification] = []
        for cert_id in certification_ids:
            cert_record = CertificateService.get_certification(cert_id)
            if not cert_record:
                logger.warning(f"Certification {cert_id} not found, skipping")
                continue

            resume_certifications.append(
                ResumeCertification(
                    title=cert_record.title,
                    date=cert_record.date,
                )
            )

        # Create complete ResumeData
        resume_data = ResumeData(
            name=f"{user.first_name} {user.last_name}",
            title=title,
            email=user.email or "",
            phone=user.phone_number or "",
            linkedin_url=user.linkedin_url or "",
            professional_summary=professional_summary,
            experience=resume_experiences,
            education=resume_education,
            skills=skills,
            certifications=resume_certifications,
        )

        # Create new version
        new_version = ResumeService.create_version(
            job_id=job_id,
            resume_data=resume_data,
            template_name=template_name,
            event_type="generate",
            parent_version_id=parent_version_id,
        )

        if not new_version.id:
            raise ValueError("Failed to create resume version")

        # Track version_id for return to caller via injected tracker
        version_tracker["version_id"] = new_version.id

        logger.info(
            "Created new resume draft from AI proposal",
            extra={"job_id": job_id, "version_id": new_version.id},
        )

        # Return confirmation message for AI and version_id as artifact
        return f"Resume Draft Created: {new_version.id}", new_version.id

    except Exception as exc:
        logger.exception("Failed to create resume draft: %s", exc)
        raise


# ==================== Chain Definition ====================

_llm = get_model(OpenAIModels.gpt_4o)
_llm_with_tools = _llm.bind_tools([propose_resume_draft])
_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT_TEMPLATE),
            ("placeholder", "{message_history}"),
        ]
    )
    | _llm_with_tools
)
