from __future__ import annotations

from langchain_core.prompts.chat import ChatPromptTemplate
from openai import APIConnectionError
from pydantic import BaseModel, Field

from src.core.models import OpenAIModels, get_model
from src.logging_config import logger

from ..state import InternalState, PartialInternalState
from .utils import format_experiences_for_prompt


def generate_summary(state: InternalState) -> PartialInternalState:
    """
    Generate a professional title and summary for a resume grounded in the user's experience and free-form responses to career-related questions, targeted for a specific job description.

    This node analyzes the job description, work experience, and additional responses to generate a professional title and summary that are aligned with the target role. The LLM uses structured output to ensure the title and summary are concise, relevant, and aligned with the job description.

    Implementation Requirements:
    - Validate required inputs (job_description, experiences, responses) early
    - Use structured LLM output to ensure consistent format
    - Format experience data appropriately for the prompt
    - Return only the title and professional_summary fields in PartialInternalState
    - Handle LLM errors gracefully with retry logic
    - Log node execution for debugging
    - Generate a professional title and summary that are aligned with the target role
    """
    logger.debug("NODE: generate_summary")

    # Validate required inputs
    if not state.job_description:
        raise ValueError("job_description is required for summary generation")
    if not state.experiences:
        raise ValueError("experiences list cannot be empty for summary generation")

    # Format experiences for the prompt
    formatted_experiences = format_experiences_for_prompt(state.experiences)

    # Generate title and summary using LLM (structured output)
    response = chain.invoke(
        {
            "job_description": state.job_description,
            "experiences": formatted_experiences,
            "responses": state.responses or "",
            "special_instructions": state.special_instructions or "",
            "resume_draft": str(state.resume_draft) if state.resume_draft is not None else "",
        }
    )

    validated = SummaryOutput.model_validate(response)

    return PartialInternalState(title=validated.title, professional_summary=validated.professional_summary)


# Prompt templates
system_prompt = """
    # Professional Summary Generator

    **Role**: You are an expert resume writer and career strategist. Your task is to generate a concise, compelling `Title` and `Professional Summary` for a candidate's resume that will capture a hiring manager's attention and communicate immense value in seconds.

    **Inputs**:
    1.  `<Job Description>`: The target job description the candidate is applying for.
    2.  `<Work Experience>`: The candidate's detailed work history, including roles, responsibilities, and achievements.
    3.  `<Candidate Responses>`: Free-form answers from the candidate detailing their interests, motivations, values, or specific reasons for applying for this role.
    4.  `<Resume Draft>`: This is the current content of the existing resume. Use it to maintain narrative consistency and avoid conflicting or duplicative statements.
    5.  `<Special Instructions>` (optional): Additional guidance or constraints from the user (tone, emphasis, exclusions). Apply when not conflicting with factual grounding or legality.

    **Objective**:
    Create a professional `Title` and `Summary` that are strictly aligned with the `<Job Description>` and grounded in the evidence provided. The summary must be a powerful, scannable distillation of the candidate's unique value, structured for maximum impact.

    ---

    ### **Core Instructions & Principles**

    1.  **Create a Modern, Scannable Title**:
        *   Synthesize the target role and the candidate's experience into a modern, clear title.
        *   Use separators like `|` or `,` to concisely combine a core role with a key specialization. Examples: `Senior Accountant | Financial Controls`, `AI Engineer | Agentic Systems`, `Registered Nurse, BSN`.

    2.  **Job Description as the Ultimate Filter**:
        *   This is the most important rule. The `<Job Description>` is your primary filter. Every skill, technology, or achievement you select from the candidate's background **must directly map to a stated need, qualification, or keyword in the job description.**
        *   If a detail from the candidate's experience is not relevant to the target role, **it must be excluded.**

    3.  **Follow a Strict Narrative Structure & Rhythm**:
        *   You must tell a miniature story in **2-3 short, balanced sentences.** This creates a clear reading rhythm.
        *   **CRITICAL FAILURE TO AVOID:** Do not create a long "laundry list" sentence that crams multiple features, skills, or actions together with "and" or dashes.
        *   **Sentence 1 (Identity & Specialization):** Direct statement of specialization.
        *   **Sentence 2 (Proof of Capability):** A concrete project example to *demonstrate capability*, not to list every feature.
        *   **Sentence 3 (Quantified Impact):** The single most powerful, relevant metric, framed as an active achievement.

    4.  **Synthesize Details into Capabilities (Summarize, Don't List)**:
        *   Instead of listing every feature of a project, you must synthesize them into a high-level statement of capability.
        *   Follow the "Rule of Three": Select no more than three of the most important and relevant details to highlight. This forces prioritization and prevents the summary from becoming a dense, unreadable list.

    5.  **Prioritize the Top Relevant Metric**:
        *   Select only the single most compelling metric that is **most relevant to the goals of the target role.** After stating the powerful metric, stop. Do not explain its obvious implications (e.g., "...enabling near-real-time updates").

    6.  **Use a Professional, Active Voice**:
        *   **Implied First-Person (No Pronouns):** Omit all personal pronouns ('I,' 'me,' 'he,' 'she').
        *   **Active Voice Only:** Always use the active voice (`Reduced costs by 15%`, not `Costs were reduced by 15%`).
        *   **Tense Usage:** Use present tense for identity/skills (`specializing in...`) and past tense for completed achievements (`launched...`).

    7.  **Avoid Clichés, Buzzwords, and Fluff**:
        *   Eliminate all generic buzzwords: `results-driven`, `team player`, `hard-working`, `detail-oriented`, etc.

    ---

    ### **If Special Instructions Are Provided**
    -   Treat `<Special Instructions>` as user guidance for tone, emphasis, exclusions, or constraints.
    -   Apply them faithfully when they do not contradict factual grounding or the job description.
    -   Examples: emphasize leadership, avoid acronyms, use UK English, highlight healthcare projects, cap summary at 3 sentences, etc.

    ### **High-Quality Professional Summary Examples with Analysis**

    **Example 1: Product Manager (Mid-Level)**

    *   **Weak Example (B+):** Product Manager with 5 years of experience leading the full lifecycle for B2C mobile apps. Drove development of a new social sharing feature that integrated with Facebook and Twitter APIs and allowed for photo/video uploads, resulting in a 25% increase in daily active users and a 15% uplift in user-generated content.

    *   **Strong Example (A+):**
        **Title:** Product Manager | B2C Mobile Applications
        **Professional Summary:**
        Product Manager with 5 years of experience leading the full lifecycle for consumer-facing mobile apps. Drove the development and launch of a new social sharing feature, resulting in a 25% increase in daily active users. Skilled in agile development and using data-driven insights to guide roadmap prioritization.

    *   **Why the Strong Example is Better:**
        *   **It Summarizes, Not Lists:** It avoids the "feature dump" (listing APIs, photo/video uploads) and instead presents the project as a single, high-level achievement.
        *   **Better Rhythm:** It breaks the long, dense accomplishment sentence into two shorter, more scannable sentences, creating a better reading flow.
        *   **Prioritizes the Top Metric:** It highlights the most impressive metric (25% increase in DAU) instead of diluting it with a second, less impactful one.

    **Example 2: Registered Nurse (Mid-Career)**

    *   **Weak Example (B):** A Critical Care RN with 7+ years in ICUs. Was involved in a unit-wide initiative to revise patient mobility, turning, and documentation protocols, which led to pressure ulcer incidents being reduced by 40%. Also adept at mentoring and collaboration.

    *   **Strong Example (A+):**
        **Title:** Registered Nurse, BSN | Critical Care
        **Professional Summary:**
        Critical Care RN with 7+ years of experience in high-acuity ICU environments. Spearheaded a unit-wide initiative to revise patient mobility protocols, which directly reduced pressure ulcer incidents by 40% over 18 months. Adept at mentoring junior nurses and collaborating with interdisciplinary teams to optimize patient care.

    *   **Why the Strong Example is Better:**
        *   **Uses Active Voice:** It starts with the powerful verb "Spearheaded" instead of the passive "Was involved in."
        *   **More Professional Tone:** It omits the conversational "A" at the beginning and uses more formal language ("high-acuity," "optimize patient care").
        *   **Specific and Confident:** It synthesizes the details of the initiative into a single, confident action ("revise patient mobility protocols").

    **Example 3: Marketing Coordinator (Entry-Level)**

    *   **Weak Example (B+):** Marketing Coordinator with 2 years of experience. Handled the corporate Instagram by posting 5 times a week, running contests, and creating stories, which grew the audience by 300% and increased engagement by 50%. I am skilled in Hootsuite, Canva, and Google Analytics.

    *   **Strong Example (A+):**
        **Title:** Marketing Coordinator | Digital & Social Media
        **Professional Summary:**
        Enthusiastic Marketing Coordinator with 2 years of experience supporting integrated digital campaigns. Took ownership of the corporate Instagram account, creating a content strategy that grew the audience by 300% and increased post engagement by 50% in one year. Skilled in using Hootsuite and Google Analytics to execute and track campaign performance.

    *   **Why the Strong Example is Better:**
        *   **Synthesizes Actions:** It elevates a list of tasks ("posting," "running contests") into a strategic accomplishment ("creating a content strategy").
        *   **No Pronouns:** It correctly omits the personal pronoun "I," adhering to the professional implied first-person standard.
        *   **More Dynamic Language:** It uses stronger, more professional verbs ("Took ownership," "execute and track") instead of weaker ones ("Handled").

    **Example 4: Human Resources Generalist (Early-Career)**

    *   **Weak Example (B):** HR Generalist with 3 years of experience. A new onboarding program I created improved new hire satisfaction scores by 30% and was correlated with a 10% increase in 1-year retention. I have expertise in HRIS implementation and ensuring compliance with labor laws.

    *   **Strong Example (A+):**
        **Title:** Human Resources Generalist | Talent Acquisition & Onboarding
        **Professional Summary:**
        HR Generalist with 3 years of experience managing the employee lifecycle in fast-paced tech startups. Revamped the company's onboarding program, improving new hire satisfaction scores by 30% and contributing to a 10% increase in 1-year retention. Expertise in HRIS implementation and ensuring compliance with labor laws.

    *   **Why the Strong Example is Better:**
        *   **Correct Voice & Pronouns:** It uses the proper third-person perspective and avoids personal pronouns ("I").
        *   **Better Narrative Flow:** It combines the two separate sentences about the achievement into a single, powerful statement with a clear cause and effect.
        *   **Stronger Verb:** "Revamped" is a more dynamic and impactful verb than "created."

    **Example 5: Journeyman Electrician (Experienced Professional)**

    *   **Weak Example (B+):** Licensed Journeyman Electrician with over 15 years of experience. Managed a crew of five on a 50,000 sq. ft. manufacturing facility project that was completed two weeks ahead of schedule. A perfect safety record was maintained across all projects by adhering to OSHA standards.

    *   **Strong Example (A+):**
        **Title:** Journeyman Electrician | Commercial & Industrial Projects
        **Professional Summary:**
        Licensed Journeyman Electrician with over 15 years of experience leading complex commercial and industrial installations. Managed a crew of five to complete the full electrical fit-out for a 50,000 sq. ft. manufacturing facility two weeks ahead of schedule. Maintained a perfect safety record across all projects through rigorous adherence to OSHA standards.

    *   **Why the Strong Example is Better:**
        *   **Active Voice Throughout:** The final sentence is in the active voice ("Maintained a perfect safety record") instead of the weaker passive voice ("A perfect safety record was maintained").
        *   **More Specific Language:** It provides more context and specificity ("leading complex...installations," "complete the full electrical fit-out"), which adds authority.
        *   **Confident Tone:** The language is more direct and confident, framing the candidate as a leader.

    **Example 6: Digital Marketing Manager (Experienced Professional)**

    *   **Weak Example (B+):** Digital Marketing Manager with 8 years of experience. Launched a multi-channel demand generation campaign using SEO, paid search, email automation, and content syndication that improved MQL to SQL conversion by 20% and increased lead volume by 45%, showing a strong ability to drive pipeline growth.

    *   **Strong Example (A+):**
        **Title:** Digital Marketing Manager | B2B Demand Generation
        **Professional Summary:**
        Digital Marketing Manager with 8 years of experience specializing in B2B demand generation for the tech sector. Developed and executed a multi-channel demand generation strategy targeting key enterprise accounts. This initiative successfully grew the sales pipeline by increasing inbound lead volume by 45% in just six months.

    *   **Why the Strong Example is Better:**
        *   **It Synthesizes the Feature Dump:** It replaces the long list of tactics (`SEO`, `paid search`, etc.) with a clean, high-level summary (`multi-channel demand generation strategy`).
        *   **It Has a Clean Narrative Rhythm:** It uses three balanced, scannable sentences instead of one long, dense sentence packed with details.
        *   **It Lets the Metric Speak for Itself:** It prioritizes the most impressive metric (45% lead volume) and removes the redundant explanatory clause ("...showing a strong ability to drive pipeline growth").

    **Example 7: HR Manager (Experienced Professional)**

    *   **Weak Example (B+):** HR Manager with 10 years of experience in the tech industry. Led a company-wide project to streamline the hiring process—implementing a new ATS (Greenhouse), training managers on best practices, and creating structured interview questions—which reduced the average time-to-hire by 35%, a significant improvement for the company.

    *   **Strong Example (A+):**
        **Title:** HR Manager | Talent Strategy & Operations
        **Professional Summary:**
        Strategic HR Manager with 10 years of experience specializing in talent strategy for high-growth tech companies. Overhauled the end-to-end talent acquisition process, centered on the implementation of the Greenhouse ATS to create a more efficient and structured hiring system. This initiative successfully reduced the average time-to-hire by 35% (from 55 to 36 days).

    *   **Why the Strong Example is Better:**
        *   **It Synthesizes the Feature Dump:** It transforms a long list of tasks (`implementing ATS`, `training`, `creating questions`) into a single, high-level strategic achievement (`Overhauled the... process`). This is the most critical improvement.
        *   **It Has a Scannable Rhythm:** It uses three balanced, focused sentences that are easy to read, unlike the weak example's single, long, and dense central sentence.
        *   **It Lets the Metric Speak for Itself:** It removes the redundant, conversational clause ("...a significant improvement for the company") and makes the metric more tangible by adding context (`from 55 to 36 days`).
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


class SummaryOutput(BaseModel):
    """Structured output for title and professional summary generation."""

    title: str = Field(description="Concise professional title for the resume header")
    professional_summary: str = Field(description="3-4 sentence professional summary tailored to the role")


llm = get_model(OpenAIModels.gpt_4o)
llm_structured = llm.with_structured_output(SummaryOutput).with_retry(retry_if_exception_type=(APIConnectionError,))
chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", user_prompt),
        ]
    )
    | llm_structured
)
