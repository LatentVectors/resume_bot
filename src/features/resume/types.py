from __future__ import annotations

from pydantic import BaseModel, Field


class ResumeData(BaseModel):
    """Complete resume data structure."""

    name: str = Field(..., description="Full name")
    title: str = Field(..., description="Professional title")
    email: str = Field(..., description="Email address")
    phone: str = Field(..., description="Phone number")
    linkedin_url: str = Field(..., description="LinkedIn profile URL")
    professional_summary: str = Field(..., description="Professional summary/objective")
    experience: list[ResumeExperience] = Field(
        default_factory=list, description="List of work experiences"
    )
    education: list[ResumeEducation] = Field(
        default_factory=list, description="List of educational background"
    )
    skills: list[str] = Field(default_factory=list, description="List of skills and technologies")
    certifications: list[ResumeCertification] = Field(
        default_factory=list, description="List of certifications"
    )

    def __str__(self) -> str:
        """Return a readable, formatted string representation suitable for output.

        This mirrors a simple resume layout for downstream consumers and logging.
        """
        lines: list[str] = []
        lines.append(f"{self.name}")
        lines.append(f"{self.title}")
        lines.append(f"Email: {self.email} | Phone: {self.phone} | LinkedIn: {self.linkedin_url}")
        lines.append("")

        if self.professional_summary:
            lines.append("Professional Summary")
            lines.append(self.professional_summary)
            lines.append("")

        if self.experience:
            lines.append("Experience")
            for exp in self.experience:
                lines.append(f"- {exp.title} at {exp.company} ({exp.start_date} - {exp.end_date})")
                for point in exp.points:
                    lines.append(f"  • {point}")
            lines.append("")

        if self.skills:
            lines.append("Skills")
            lines.append(", ".join(self.skills))
            lines.append("")

        if self.education:
            lines.append("Education")
            for edu in self.education:
                lines.append(
                    f"- {edu.degree} in {edu.major} — {edu.institution} ({edu.grad_date})"
                )
            lines.append("")

        if self.certifications:
            lines.append("Certifications")
            for cert in self.certifications:
                lines.append(f"- {cert.title} ({cert.date})")

        return "\n".join(lines).strip()

    def __repr__(self) -> str:
        """Debug-friendly representation summarizing key fields."""
        exp_count = len(self.experience)
        edu_count = len(self.education)
        cert_count = len(self.certifications)
        skills_count = len(self.skills)
        return (
            "ResumeData("
            f"name={self.name!r}, title={self.title!r}, "
            f"experience={exp_count}, education={edu_count}, "
            f"skills={skills_count}, certifications={cert_count})"
        )


class ResumeExperience(BaseModel):
    """Work experience information for a resume."""

    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    start_date: str = Field(..., description="Start date of employment")
    end_date: str = Field(..., description="End date of employment (or 'Present')")
    points: list[str] = Field(default_factory=list, description="List of experience points")


class ResumeEducation(BaseModel):
    """Education information for a resume."""

    degree: str = Field(..., description="The degree obtained")
    major: str = Field(..., description="The field of study")
    institution: str = Field(..., description="The educational institution")
    grad_date: str = Field(..., description="Graduation date")


class ResumeCertification(BaseModel):
    """Certification information for a resume."""

    title: str = Field(..., description="The certification title")
    date: str = Field(..., description="The date the certification was obtained")
