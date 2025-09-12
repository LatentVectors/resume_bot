# Overview
Use LLMs to generate a resume 

# State
Input
- job_description: str
- experiences: list[Experience]
- responses: str

Output
- resume: str

# Nodes
**Generate Summary**
Generate a professional summary grounded in the users experience and free-form responses to career-related questions, targeted for a specific job description.
Use an LLM to return a short, impactful, professional summary.

Experience:
    - company: str
    - title: str
    - start_date: date
    - end_date: date | None
    - content: str
    - points: list[str]

Reads:
- job_description: str
- experiences: list[Experience]
- responses: str

Returns:
- professional_summary: str

**Generate Experience**
Generate experience bullet points for a resume grounded in the users experience and free-form responses to career-related questions, targeted for a specific job description.
Use an LLM to return a short, impactful bullet points for the provided experience.
Merge the bullet points into the existing experience objects using structured LLM outputs to match the bullet points to the source experience.

Reads:
- job_description: str
- experiences: list[Experience]
- responses: str

Returns:
- experiences: list[Experience]

**Generate Skills**
Generate a list of skills for a resume grounded in the users experience and free-form responses to career-related questions, targeted for a specific job description.
Use an LLM to return a list of skills the candidate has that align with the job description.

Reads:
- job_description: str
- experiences: list[Experience]
- responses: str

Returns:
- skills: list[str]

**Create Resume**

Reads:
- professional_summary
- experiences
- skills

Returns:
- resume: str


# Graph
start -> generate_summary 
start -> generate_experience 
start -> generate_skills 
generate_summary -> create_resume
generate_experience -> create_resume
generate_skills -> create_resume
create_resume -> end
