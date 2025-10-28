"""Gap analysis feature for matching job requirements to user experience.

This module provides functionality to analyze the fit between a job description
and a user's experience, identifying matched requirements, partial matches, gaps,
and suggesting clarifying questions.
"""

from __future__ import annotations

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts.chat import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig

from app.constants import LLMTag
from app.shared.formatters import format_experience_with_achievements
from src.core.models import OpenAIModels, get_model
from src.database import Experience, db_manager
from src.logging_config import logger


def analyze_job_experience_fit(job_description: str, experiences: list[Experience]) -> str:
    """Analyze how well user experiences match a job description.

    Uses an LLM to extract job requirements and match them against user experience,
    producing a structured report of matches, partial matches, gaps, and suggested
    questions for further clarification.

    Args:
        job_description: The full text of the job description to analyze
        experiences: List of user Experience objects to evaluate

    Returns:
        String containing matched requirements, partial matches, gaps,
        and suggested questions. On error, returns a report with has_error=True
        and empty lists.
    """
    try:
        if not job_description or not job_description.strip():
            logger.warning("Gap analysis called with empty job description")
            return ""

        experience_summary = _format_experience_for_analysis(experiences)

        config = RunnableConfig(
            tags=[LLMTag.GAP_ANALYSIS.value],
        )

        result = _chain.invoke(
            {
                "job_description": job_description,
                "work_experience": experience_summary,
            },
            config=config,
        )

        if not result or not result.strip():
            logger.warning("Gap analysis returned empty result from LLM")
            return ""

        return result

    except Exception as exc:
        # Broad catch to prevent errors from bubbling to UI
        logger.exception(
            "Gap analysis failed with exception. Job description length: %d, Experience count: %d, Error: %s",
            len(job_description) if job_description else 0,
            len(experiences),
            exc,
        )
        return ""


def _format_experience_for_analysis(experiences: list[Experience]) -> str:
    """Format experience records into a readable summary for the LLM.

    Args:
        experiences: List of Experience objects to format

    Returns:
        Formatted string summarizing the user's experience
    """
    if not experiences:
        return "No work experience provided."

    formatted_parts: list[str] = []

    for exp in experiences:
        # Fetch achievements for this experience
        achievements = db_manager.list_experience_achievements(exp.id)
        # Use the standardized formatter
        formatted = format_experience_with_achievements(exp, achievements)
        formatted_parts.append(formatted)

    return "\n\n".join(formatted_parts)


_SYSTEM_PROMPT = """
# **Job Fit Analysis**

## **Objective**

Your goal is to conduct a comprehensive analysis of a user's provided `<work_experience>` document against a specific `<job_description>`. The output will be a structured report detailing the user's fit for the role, highlighting strengths, areas for improvement, and potential gaps.

## **Persona**

You are a **strategic career analyst**. Your task is to provide a clear, objective, and detailed comparison between the user's experience and the requirements of the job description.

## **Key Instructions**

*   **Uphold Absolute Honesty:** Do not extrapolate, exaggerate, or overstate the user's experience. Every point of alignment must be directly supported by evidence from the `<work_experience>` document. If the evidence is indirect, it must be categorized under 'Areas to Strengthen and Reframe'.
*   **Comprehensive Coverage:** Your report must address **every requirement** outlined in the job description. This includes all skills, qualifications, responsibilities, expectations, and any other criteria mentioned. Every point from the job description must be categorized in your final report.
*   **Analyze Qualitative and Cultural Fit:** In addition to technical skills and direct experience, analyze the job description for indicators of personality, work culture (e.g., 'fast-paced environment,' 'strong collaboration'), and industry alignment. Attempt to connect these qualitative aspects to evidence within the user's `<work_experience>`.
*   **Evidence-Based Analysis:** Your analysis must be based *only* on the information provided in the user's `<work_experience>` document and the `<job_description>`. Do not make assumptions.
*   **Strategic Focus:** When conducting your analysis, prioritize the user's most recent and relevant roles. While you should consider their entire history, the focus of your justifications should be on the experience that most directly aligns with the target job.
*   **Strict Adherence to Format:** Your entire response must strictly follow the output format defined below.

---

## **Required Output Format**

Your response must strictly follow this Markdown structure:

```markdown
[A brief, 1-3 sentence summary of the user's overall fit for the role based on the documents provided.]

---

### **Strategic Report: Experience vs. Job Description**

#### **Part 1: Areas of Strong Alignment**
*   **"[Direct Quote from Job Description]":** [Provide a brief justification for the alignment, citing a specific example from the user's work experience document.]
*   *(Repeat this format for all identified areas of strong alignment.)*

#### **Part 2: Areas to Strengthen and Reframe**
*   **"[Direct Quote from Job Description]":** [Provide a brief justification explaining why the user's experience is a partial or indirect match that could be better highlighted or reframed.]
*   *(Repeat this format for all identified areas that need strengthening or reframing.)*

#### **Part 3: Potential Gaps to Address**
*   **"[Direct Quote from Job Description]":** [Note that this specific requirement appears to be absent from the provided work experience document.]
*   *(Repeat this format for all identified potential gaps.)*
```
"""

_USER_PROMPT = """
<job_description>
{job_description}
</job_description>

<work_experience>
{work_experience}
</work_experience>

Analyze the fit between this job and the candidate's experience.
"""


# Model and chain setup
_llm = get_model(OpenAIModels.gpt_4o)
_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", _SYSTEM_PROMPT),
            ("user", _USER_PROMPT),
        ]
    )
    | _llm
    | StrOutputParser()
)
