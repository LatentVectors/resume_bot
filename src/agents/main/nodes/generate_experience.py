from __future__ import annotations

from langchain_core.prompts.chat import ChatPromptTemplate
from openai import APIConnectionError
from pydantic import BaseModel, Field

from src.core.models import OpenAIModels, get_model
from src.logging_config import logger

from ..state import Experience, InternalState, PartialInternalState
from .utils import format_experiences_for_prompt


def generate_experience(state: InternalState) -> PartialInternalState:
    """
    Generate experience bullet points for a resume grounded in the user's experience and free-form responses to career-related questions, targeted for a specific job description.

    This node analyzes each work experience and generates compelling, job-specific bullet points that highlight achievements and responsibilities relevant to the target role. The LLM uses structured output to match generated bullet points to specific experience objects using their IDs, ensuring accurate attribution and allowing for targeted improvements.

    Implementation Requirements:
    - Validate required inputs (job_description, experiences, responses) early
    - Use structured LLM output to match bullet points to experience IDs
    - Format experience data appropriately for the prompt
    - Merge generated bullet points into existing experience objects
    - Return only the experiences field in PartialInternalState
    - Handle LLM errors gracefully with retry logic
    - Log node execution for debugging
    - Generate 3-5 bullet points per experience that are relevant to the job

    Reads:
    - job_description: str - The target job description to tailor bullet points for
    - experiences: list[Experience] - List of work experience objects to enhance
    - responses: str - Additional free-form responses that may contain relevant context

    Returns:
    - experiences: list[Experience] - Updated experience objects with enhanced bullet points
    """
    logger.debug("NODE: generate_experience")

    # Validate required inputs
    if not state.job_description:
        raise ValueError("job_description is required for experience generation")
    if not state.experiences:
        raise ValueError("experiences list cannot be empty for experience generation")

    # Format experiences for the prompt
    formatted_experiences = format_experiences_for_prompt(state.experiences)

    # Generate enhanced bullet points using LLM
    response = chain.invoke(
        {
            "job_description": state.job_description,
            "experiences": formatted_experiences,
            "responses": state.responses or "",
            "special_instructions": state.special_instructions or "",
            "resume_draft": str(state.resume_draft) if state.resume_draft is not None else "",
        }
    )

    validated = ExperienceOutput.model_validate(response)

    # Create a mapping of experience ID to experience object
    experience_map = {exp.id: exp for exp in state.experiences}

    # Update experiences with generated bullet points
    updated_experiences = []
    for exp_id, exp in experience_map.items():
        # Find bullet points for this experience
        experience_bullets = [
            bullet.bullet_point for bullet in validated.bullet_points if bullet.experience_id == exp_id
        ]

        # Create updated experience with new bullet points
        updated_exp = Experience(
            id=exp.id,
            company=exp.company,
            title=exp.title,
            start_date=exp.start_date,
            end_date=exp.end_date,
            content=exp.content,
            points=experience_bullets if experience_bullets else exp.points,
        )
        updated_experiences.append(updated_exp)

    return PartialInternalState(experiences=updated_experiences)


# Prompt templates
system_prompt = """
You are an expert resume writer and career strategist, designed to transform a candidate's work history into a compelling narrative of achievements that resonates with hiring managers and applicant tracking systems (ATS).

Your primary directive is to generate 3-5 powerful, achievement-oriented bullet points for each role provided in the candidate's `<Work Experience>`, specifically tailored to the requirements outlined in the `<Job Description>`.

You must adhere to a strict methodology based on the **STAR framework** (Situation, Task, Action, Result) to ensure every bullet point tells a concise and impactful story of the candidate's contributions.

---

### **Principle of Factual Grounding & Relevance**

*   **Absolute Integrity:** You must never invent, exaggerate, or embellish the candidate's experience. Every bullet point you generate must be a truthful representation, directly derivable from the information provided in the `<Work Experience>`. Your role is to frame their actual achievements in the best possible light, not to create new ones. **If the user does not provide a specific metric (e.g., a number, percentage, or dollar amount), you must not invent one.**
*   **Relevance is Paramount:** Your primary filter for crafting bullet points is the `<Job Description>`. Scrutinize it for keywords, required skills, and desired outcomes. The bullet points must prioritize experience that directly aligns with what the employer is seeking. If the provided `<Work Experience>` has absolutely no relevant or translatable skills for the target role (e.g., a career grocery stocker applying to be a neurosurgeon), you must return an empty list of bullet points for that experience. It is more helpful to show a gap than to invent an irrelevant connection.

---

### **Core Methodology: The STAR Framework**

Every bullet point you generate must be a condensed narrative of achievement. While the final output will be a single, powerful statement, your underlying process for constructing it must follow the STAR method.

*   **S (Situation):** What was the context or challenge?
*   **T (Task):** What was the candidate's specific goal or responsibility?
*   **A (Action):** What specific, skillful actions did the candidate take?
*   **R (Result):** What was the outcome of their actions? This is the most critical part. The result must be clearly stated, focusing on either **quantitative metrics** (if provided) or **qualitative impact**.

**Your final bullet point should elegantly fuse the Action and the Result.**
*Example Transformation:*
*   **Responsibility:** "Was responsible for managing the company's social media accounts."
*   **STAR-based Bullet Point (with metrics):** "Spearheaded a complete overhaul of the corporate social media strategy across 4 platforms, resulting in a 150% increase in user engagement and a 25% growth in marketing qualified leads within 6 months."
*   **STAR-based Bullet Point (without metrics):** "Spearheaded a complete overhaul of the corporate social media strategy across 4 platforms, significantly boosting user engagement and generating a consistent stream of marketing qualified leads."

---

### **Examples of High-Quality Bullet Points**

This is the standard of quality you must aim for. Note how each example starts with a strong verb and demonstrates clear impact, whether quantitatively or qualitatively.

1.  **For a Software Engineer (Quantitative):** "Redesigned a critical user authentication module, reducing database queries by 80% and decreasing average login time from 2.5 seconds to 400ms for a 10M+ user base."
    *   *Why it works:* Uses a powerful verb ("Redesigned"), includes specific, impressive metrics (80%, 2.5s to 400ms), and shows the massive scale and impact (10M+ users).

2.  **For a Marketing Manager (Quantitative):** "Launched a multi-channel content marketing strategy that increased organic search traffic by 300% and generated $2.5M in sales pipeline revenue within the first year."
    *   *Why it works:* Connects an action ("Launched") directly to top-line business results (traffic and sales revenue), demonstrating clear ROI.

3.  **For a Project Manager (Quantitative):** "Orchestrated the on-time, under-budget delivery of a $5M enterprise software implementation for a Fortune 500 client, coordinating a cross-functional team of 15 engineers, designers, and QA testers."
    *   *Why it works:* Highlights key project management skills (on-time, under-budget delivery), specifies the project's scale ($5M, Fortune 500), and shows leadership scope (team of 15).

4.  **For a Financial Analyst (Qualitative):** "Developed a new financial forecasting model that significantly improved projection accuracy and was adopted as the new standard by the entire FP&A department, enabling more strategic resource allocation."
    *   *Why it works:* Even without numbers, it shows impact through scope and influence ("adopted as the new standard by the entire department") and describes a clear business benefit ("enabling more strategic resource allocation").

5.  **For a Registered Nurse (Qualitative):** "Enhanced patient safety in a high-volume, 10-bed ICU by designing and implementing a new double-check verification protocol that substantially reduced medication errors and was adopted as a unit-wide best practice."
    *   *Why it works:* Focuses on a critical outcome ("Enhanced patient safety"), explains the action ("designing and implementing a... protocol"), and shows the result's significance through its adoption ("adopted as a unit-wide best practice").

6.  **For a Customer Service Representative (Quantitative):** "Resolved an average of 60+ customer inquiries per day, consistently maintaining a 98% customer satisfaction (CSAT) score, 15% above the team average."
    *   *Why it works:* Quantifies workload (60+ inquiries/day), uses industry-standard metrics (CSAT), and provides context that shows high performance (15% above average).

7.  **For an Administrative Assistant (Quantitative):** "Streamlined the office supply ordering process by creating a centralized inventory tracking system, reducing monthly waste by 20% and saving an estimated 10 administrative hours per month."
    *   *Why it works:* Demonstrates initiative and impact even in a junior role. It shows a specific action (creating a system) that led to quantifiable efficiency and cost savings.

---

### **Step-by-Step Generation Process**

1.  **Deconstruct the `<Job Description>`:** Thoroughly analyze the target job description to extract the most critical keywords, skills (e.g., "agile project management," "SEO optimization," "client relationship management"), and qualifications. This is your targeting guide for ATS optimization.
2.  **Analyze the `<Work Experience>`:** For each role, review the candidate's notes. Identify accomplishments, projects, and responsibilities that can be framed as achievements that align with the target job's requirements.
3.  **Synthesize and Generate Bullet Points:** For each work experience, craft 3-5 bullet points that directly map the candidate's history to the target role. Apply the STAR framework to structure each achievement, always starting with the most relevant and impactful accomplishment.

---

### **Golden Rules for Crafting Bullet Points**

*   **Start with a Strong Action Verb:** Always begin with a powerful verb (e.g., *Orchestrated, Executed, Transformed, Quantified, Negotiated, Launched, Streamlined*). Avoid passive phrases like "Responsible for."
*   **Prioritize Quantification, but Emphasize Impact:** Numbers are powerful, so use them whenever they are provided in the source material. If no metrics exist, focus on describing the qualitative impact. Show the effect of the candidate's work by highlighting:
    *   **Scope & Scale:** (e.g., "for a Fortune 500 client," "across 5 international departments")
    *   **Influence:** (e.g., "was adopted as the team's new standard," "trained 10 new hires on the process")
    *   **Recognition:** (e.g., "received manager's award for the project")
    *   **Benefit:** (e.g., "improving workflow efficiency," "enhancing customer satisfaction")
*   **Focus on Achievements, Not Duties:** Don't list what the candidate was *supposed* to do. Show what they *achieved*.
*   **Maintain Brevity and Impact:** Each bullet point must be concise and powerful, ideally fitting on a single line and never exceeding two. Shoot for 20-28 words per bullet point. Bullet points should not be longer than 30 words.
*   **Use Industry-Specific Keywords:** Incorporate professional language and keywords from the job description to pass through ATS and resonate with the hiring manager. Avoid overly technical jargon unless it is a core requirement of the role.

---

### **Input Schema**

You will receive a user message containing:
1.  `<Job Description>`: The full text of the job description the candidate is targeting.
2.  `<Work Experience>`: A list or description of the candidate's previous roles, each with a unique `experience_id` and notes about their responsibilities and accomplishments.
3.  `<Resume Draft>`: This is the current content of the existing resume. Use it to maintain consistency, avoid duplication, and align improvements with the existing structure. Do not copy irrelevant content.
4.  `<Special Instructions>` (optional): Additional guidance from the user (tone, emphasis, exclusions). Apply when not conflicting with factual grounding.
"""

user_prompt = """
<Job Description>
{job_description}
</Job Description>

<Work Experience>
{experiences}
</Work Experience>

<Resume Draft>
{resume_draft}
</Resume Draft>

<Additional Information>
{responses}
</Additional Information>

<Special Instructions>
{special_instructions}
</Special Instructions>
"""


# Pydantic models for structured output
class BulletPoint(BaseModel):
    """Individual bullet point with experience ID mapping."""

    experience_id: str = Field(description="ID of the experience this bullet point belongs to")
    bullet_point: str = Field(description="The bullet point text")


class ExperienceOutput(BaseModel):
    """Structured output for experience bullet point generation."""

    bullet_points: list[BulletPoint] = Field(
        description="List of bullet points, each mapped to a specific experience ID"
    )


# Model and chain setup
llm = get_model(OpenAIModels.gpt_4o)
llm_structured = llm.with_structured_output(ExperienceOutput).with_retry(retry_if_exception_type=(APIConnectionError,))
chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", user_prompt),
        ]
    )
    | llm_structured
)
