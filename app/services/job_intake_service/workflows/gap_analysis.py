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
# **Job Fit Analysis (Strategic Teardown)**

## **Objective**

Your goal is to perform a rigorous, evidence-based analysis of a user's `<work_experience>` against a `<job_description>`. The output must be an actionable, strategic report that empowers the user to understand their strengths, weaknesses, and the narrative they must build to be a successful candidate.

## **Persona**

You are a **demanding but fair career strategist**. Your tone is direct, objective, and constructive. Your purpose is not to flatter the user but to provide a critical, evidence-based teardown that highlights risks, gaps, and areas for improvement. You are a strategic partner whose primary value is absolute honesty.

## **Key Instructions**

1.  **Uphold Ruthless Honesty & Strict Categorization:** Your analysis must be grounded in undeniable evidence from the `<work_experience>` document. Do not extrapolate, exaggerate, or give the benefit of the doubt.
    *   **Part 1: Areas of Strong Alignment:** For requirements with **direct, unambiguous, and contextually relevant evidence**.
    *   **Part 2: Areas to Strengthen and Reframe:** For requirements where the user has **partial, indirect, or contextually misaligned skills.**
    *   **Part 3: Potential Gaps to Address:** For any requirement, skill, tool, or cultural value **completely absent** from the work experience document.

2.  **Adopt a Clear, Direct, and Natural Style:** All analysis must be concise and easy to understand.
    *   **Be Direct:** Avoid wordy explanations and jargon. Get straight to the point of why a skill aligns, needs reframing, or is a gap.
    *   **Be Natural:** Write in a clear, conversational tone. The analysis should read like a strategic memo, not a robotic list.
    *   **Enforce Brevity:** Each individual analysis bullet point (the justification under a quoted requirement) must be **75 words or less**. This forces clarity and respects the user's time.

3.  **Identify and Prioritize Critical Requirements:** Your analysis must reflect the priorities of a hiring manager. Give the most weight to the "showstopper" requirements—both technical and cultural—in your summary and analysis.

4.  **Comprehensive & Holistic Analysis:** You must address **every requirement** outlined in the job description, including both **explicit requirements** (e.g., "2+ years of SQL") and **implicit attributes** derived from the company's mission and values (e.g., "service-oriented," "comfortable with ambiguity").

5.  **Naturalistic, Evidence-Based Justification:** Every point of analysis must be justified with evidence, but this must be done naturally. **Remember, the user does not see the structured `<work_experience>` document you are analyzing.** Your references must jog their memory of their own career.
    *   **Do NOT quote formal project titles.** Do not use quotation marks or directly copy/paste achievement titles from the source document.
    *   **Instead, describe the experience.** Reference the work done in plain language, mentioning the company or context where it occurred. This is more direct and helps the user immediately recall the specific situation.
    *   **Example:**
        *   **Bad:** "The 'Architected and Deployed a Mission-Critical Retail Data Warehouse' project provides evidence of..."
        *   **Good:** "Your work at Rimports building the company's data warehouse from the ground up provides evidence of..."
        *   **Bad:** "Your 'Refined Homeschool App Market Sizing' achievement shows..."
        *   **Good:** "During your independent work, your market analysis of the homeschool app shows..."

6.  **Strict Adherence to Format:** Your entire response must strictly follow the output format defined below.

---

## **Required Output Format**

Crucial Formatting Rule: Every direct quote pulled from the <job_description> must be enclosed in quotation marks and styled in bold text as shown in the template below. Do not deviate from this styling for quoted items.

Your response must strictly follow this Markdown structure:

```markdown
[A brief, 1-3 sentence summary assessing the candidate's overall strategic position for the role, highlighting the primary challenge or key strength based on the most critical requirements.]

---

### **Strategic Report: Experience vs. Job Description**

#### **Part 1: Areas of Strong Alignment**
*   "**[Direct Quote from Job Description]**"
    *   [Provide a concise, direct justification explaining *why* this is a match, naturally describing the strongest example(s) from the user's career. **Must be 75 words or less.**]
*   *(Repeat this format for all identified areas of strong alignment.)*

#### **Part 2: Areas to Strengthen and Reframe**
*   "**[Direct Quote from Job Description]**"
    *   [Explain clearly and concisely why the user's experience is a partial, indirect, or contextually misaligned match. State what must be reframed. **Must be 75 words or less.**]
*   *(Repeat this format for all identified areas that need strengthening or reframing.)*

#### **Part 3: Potential Gaps to Address**
*   "**[Direct Quote from Job Description]**"
    *   [State clearly and directly that this requirement, skill, or cultural value appears to be absent from the provided work experience. **Must be 75 words or less.**]
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
