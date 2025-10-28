"""Resume generation workflow from intake conversation context.

This workflow generates initial resume drafts enriched with conversational context
from the job intake flow using structured LLM outputs.
"""

from __future__ import annotations

from langchain_core.messages import BaseMessage
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from openai import APIConnectionError

from app.constants import LLMTag
from src.core.models import OpenAIModels, get_model
from src.database import db_manager
from src.features.resume.data_adapter import fetch_experience_data, fetch_user_data
from src.features.resume.types import ResumeData
from src.logging_config import logger

# ==================== Main Workflow Function ====================


def generate_resume_from_conversation(
    job_id: int,
    user_id: int,
    messages: list[BaseMessage],
) -> ResumeData:
    """Generate initial resume draft using intake conversation context.

    Uses structured LLM output to create a resume tailored to the job based on
    the user's experience and insights from the intake conversation.

    Args:
        job_id: ID of the job being applied to
        user_id: ID of the user
        messages: Chat message history from stage 2

    Returns:
        ResumeData ready for creating first version in intake step 3

    Raises:
        ValueError: If job or user data is invalid or missing
    """
    try:
        # Fetch job
        job = db_manager.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")

        # Fetch user data and experiences
        user_data = fetch_user_data(user_id)
        if not user_data:
            raise ValueError(f"User {user_id} not found")

        experiences = fetch_experience_data(user_id)
        if not experiences:
            raise ValueError("At least one experience record is required to generate a resume")

        config = RunnableConfig(
            tags=[LLMTag.RESUME_GENERATION.value],
            metadata={"job_id": job_id, "user_id": user_id, "source": "intake_flow"},
        )

        # Generate resume using chain
        result = _chain.invoke(
            {
                "message_history": messages,
                "name": f"{user_data.user.first_name} {user_data.user.last_name}",
                "email": user_data.user.email,
                "phone": user_data.user.phone_number or "",
                "linkedin_url": user_data.user.linkedin_url or "",
            },
            config=config,
        )
        resume_data = ResumeData.model_validate(result)

        if not resume_data:
            raise ValueError("Failed to generate resume data")

        logger.info(
            "Successfully generated resume from intake conversation",
            extra={"job_id": job_id, "user_id": user_id, "experience_count": len(experiences)},
        )

        return resume_data

    except Exception as exc:
        logger.exception("Failed to generate resume from conversation: %s", exc)
        raise


# ==================== Prompts ====================

SUMMARY_PROMPT = """
# **Resume Draft Generation**
Please generate a resume draft based on the following information.

## **Goal**
Your singular goal is to analyze the preceding conversation—including the `<work_experience>` document, the target `<job_description>`, and all dialogue—to synthesize and produce a powerful, targeted first draft of a resume.

## **My Role/Persona**
You are a **Strategic Resume Drafter**. Your expertise lies in translating a rich conversational history into a concise, tactical, and professional resume document ready for iteration.

## **Core Workflow & Principles**
1.  **Synthesize Content from History:** Your primary source material is the entire conversation history. Synthesize the most impactful stories, metrics, and details uncovered in the dialogue and the enhanced `<work_experience>` document to build the following sections:
    *   A Professional Summary
    *   A categorized Skills list
    *   A Professional Experience section

2.  **Adhere to Key Constraints:**
    *   **Uphold Absolute Honesty:** Do not embellish or exaggerate the user's experience. All content must be rooted in the information provided.
    *   **Strategic Prioritization:** Target a single-page resume by selecting only the most impactful and relevant content. A strong draft should feature **5-8 total bullet points** across all roles.
    *   **Keyword & Concept Alignment:** Prioritize using the employer's exact **keywords** and closely related concepts from the job description, bolding them in the draft.
    *   **Distill, Don't Copy:** Your task is not to copy text verbatim from the `<work_experience>` document. Instead, distill the essence of the user's accomplishments into single, high-impact resume sentences. A single bullet point might draw insights from multiple parts of the conversation.
    *   **Conciseness and Impact:** All bullet points must be single, powerful sentences focused on action, impact, and quantifiable results where possible. For the Professional Experience section, create a brief, descriptive title for each bullet point that summarizes the core competency being demonstrated.

## **User Information**
Name: {name}
Email: {email}
Phone: {phone}
LinkedIn: {linkedin_url}
"""

# ==================== Chain Definition ====================

_llm = get_model(OpenAIModels.gpt_4o)
_llm_structured = _llm.with_structured_output(ResumeData).with_retry(retry_if_exception_type=(APIConnectionError,))

_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("placeholder", "{message_history}"),
            ("user", SUMMARY_PROMPT),
        ]
    )
    | _llm_structured
)
