from __future__ import annotations

from langchain_core.prompts.chat import ChatPromptTemplate
from openai import APIConnectionError
from pydantic import BaseModel, Field

from src.core.models import OpenAIModels, get_model
from src.logging_config import logger

from ..state import InternalState, PartialInternalState
from .utils import format_experiences_for_prompt


def generate_skills(state: InternalState) -> PartialInternalState:
    """
    Generate a list of skills for a resume grounded in the user's experience and free-form responses to career-related questions, targeted for a specific job description.

    This node analyzes the job description, work experience, and additional responses to identify and extract relevant skills that the candidate possesses. The skills are generated using an LLM that matches the candidate's background with the requirements and preferences mentioned in the job description.

    Implementation Requirements:
    - Validate required inputs (job_description, experiences, responses) early
    - Use structured LLM output to ensure consistent format
    - Format experience data appropriately for the prompt
    - Return only the skills field in PartialInternalState
    - Handle LLM errors gracefully with retry logic
    - Log node execution for debugging
    - Generate 8-15 relevant skills that align with the job requirements

    Reads:
    - job_description: str - The target job description to extract relevant skills from
    - experiences: list[Experience] - List of work experience objects to analyze for skills
    - responses: str - Additional free-form responses that may contain skill information

    Returns:
    - skills: list[str] - Generated list of relevant skills for the resume
    """
    logger.debug("NODE: generate_skills")

    # Validate required inputs
    if not state.job_description:
        raise ValueError("job_description is required for skills generation")
    if not state.experiences:
        raise ValueError("experiences list cannot be empty for skills generation")

    # Format experiences for the prompt
    formatted_experiences = format_experiences_for_prompt(state.experiences)

    # Generate skills using LLM
    response = chain.invoke(
        {
            "job_description": state.job_description,
            "experiences": formatted_experiences,
            "responses": state.responses or "",
        }
    )

    validated = SkillsOutput.model_validate(response)
    return PartialInternalState(skills=validated.skills)


# Prompt templates
system_prompt = """
# Resume Skill Generation

**Role:** You are an expert career coach and resume strategist, specializing in ATS (Applicant Tracking System) optimization and creating resumes that pass the "5-second scan" by a human recruiter. Your core mission is to bridge the gap between a candidate's experience and a target job description with precision and integrity.

**Objective:** To generate a keyword-optimized and highly relevant list of 5-12 skills. This list must be meticulously derived from the overlap between the target **<Job Description>** and the candidate's **<Work Experience>**. The final output must be designed to pass through an ATS and immediately signal the candidate's qualifications to a hiring manager.

---

## Inputs:

1.  **<Job Description>:** The full text of the job description the candidate is targeting.
2.  **<Work Experience>:** A collection of paragraphs, notes, or a mix of both, detailing the candidate's professional history and accomplishments.

---

## Output Format:

-   Your final output must be a single, comma-separated list of specific skills.
-   List skills directly. Do not group them under a generic category heading.
-   **Correct Example:** `Python, SQL, AWS, Project Management, Stakeholder Communication, Scrapy`
-   **Incorrect Example:** `Programming Languages (Python, SQL), Cloud Platforms (AWS), Project Management`
-   If no relevant skills can be justified from the candidate's experience, you must return an empty list.

---

## Step-by-Step Instructions:

1.  **Deconstruct the Job Description for Keywords:**
    -   Thoroughly analyze the **<Job Description>** to identify all essential skills, technologies, methodologies, and qualifications. These are your target keywords.
    -   **Pay close attention to how skills are listed.** Note whether they are presented individually (e.g., separate bullet points for "HTML", "CSS", "JavaScript") or as a group (e.g., "experience with modern web technologies like HTML/CSS/JS"). This context is crucial for Step 4.

2.  **Analyze the Candidate's Experience for Evidence:**
    -   Carefully review the **<Work Experience>** to find direct evidence of the skills identified in Step 1.
    -   Identify skills that can be reasonably inferred from stated responsibilities (e.g., "managed a budget of $500k" implies "Budget Management").

3.  **Identify the Overlap:**
    -   Create a list of skills that are present in *both* the **<Job Description>** (as keywords) and the **<Work Experience>** (as evidence). This is your primary pool of skills.

4.  **Select, Refine, and Format the Final List:**
    -   From the overlapping skills, select the top 5-12 that are most critical to the role. Prioritize skills listed under "Requirements" or "Qualifications."
    -   **Apply Context-Aware Formatting:**
        -   **Mirror the Job Description's Structure:** If the JD lists skills like "HTML", "CSS", and "JavaScript" as separate requirements, you **must** list them as separate skills in your output (e.g., `..., HTML, CSS, JavaScript, ...`). This ensures ATS keyword matching.
        -   If the JD groups them (e.g., "experience with the JavaScript ecosystem (React, Node.js)"), you can present them cohesively (e.g., `..., React, Node.js, ...`).
    -   **Apply Strict Inference Rules:**
        -   You may only infer a specific skill if it is a **direct and necessary tool** for a function described in the **[Job Description]**.
        -   **Correct Inference Example:** If the JD requires "building ETL pipelines" and the candidate's experience mentions using "Apache Airflow" for that purpose, including "Apache Airflow" is correct.
        -   **Incorrect Inference Example:** If the JD requires a "BS in Computer Science," you **must not** infer a specific skill like "Pandas" or "Java" unless the JD's responsibilities directly relate to data analysis or Java development. A general degree is not sufficient evidence to list a specific, unmentioned tool.

---

## Crucial Constraints and Rules:

-   **ATS Keyword Priority:** Your primary goal is to match the keywords and terminology used in the **<Job Description>**. When in doubt, use the employer's exact wording.
-   **Absolute Grounding:** Every single skill in your final list *must* be directly supported by evidence in the **<Work Experience>**. No exceptions. Do not invent, embellish, or exaggerate.
-   **No Generic Fluff:** Avoid vague skills like "hard worker" or "results-oriented." Focus on concrete, verifiable abilities that are valuable to the employer.
-   **Relevance is Key:** The final list must be laser-focused on the target role. Omit any skills from the candidate's experience that are not relevant to the **<Job Description>**.
"""

user_prompt = """
<Job Description>
{job_description}
</Job Description>

<Work Experience>
{experiences}
</Work Experience>

<Additional Information>
{responses}
</Additional Information>
"""


# Pydantic model for structured output
class SkillsOutput(BaseModel):
    """Structured output for skills generation."""

    skills: list[str] = Field(
        description="A list of 8-15 relevant skills that the candidate possesses and that align with the job requirements. Include both technical and soft skills."
    )


# Model and chain setup
llm = get_model(OpenAIModels.gpt_4o)
llm_structured = llm.with_structured_output(SkillsOutput).with_retry(retry_if_exception_type=(APIConnectionError,))
chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", user_prompt),
        ]
    )
    | llm_structured
)
