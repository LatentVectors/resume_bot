import type { ResumeData } from "@resume/database/types";

/**
 * Formats a ResumeData object as plain text suitable for copying to clipboard.
 * Matches the format used in the resume editor and intake interface.
 */
export function formatResumeAsText(resume: ResumeData): string {
  let text = `${resume.name}\n${resume.title}\n\n`;
  text += `Email: ${resume.email}\n`;
  if (resume.phone) text += `Phone: ${resume.phone}\n`;
  if (resume.linkedin_url) text += `LinkedIn: ${resume.linkedin_url}\n`;
  text += `\n${resume.professional_summary}\n\n`;

  if (resume.experience && resume.experience.length > 0) {
    text += "EXPERIENCE\n";
    resume.experience.forEach((exp) => {
      text += `\n${exp.title} at ${exp.company}\n`;
      text += `${exp.start_date} - ${exp.end_date || "Present"}\n`;
      if (exp.points) {
        exp.points.forEach((point) => {
          text += `• ${point}\n`;
        });
      }
    });
  }

  if (resume.education && resume.education.length > 0) {
    text += "\nEDUCATION\n";
    resume.education.forEach((edu) => {
      text += `\n${edu.degree} in ${edu.major}\n`;
      text += `${edu.institution} - ${edu.grad_date}\n`;
    });
  }

  if (resume.skills && resume.skills.length > 0) {
    text += "\nSKILLS\n";
    text += resume.skills.join(", ") + "\n";
  }

  if (resume.certifications && resume.certifications.length > 0) {
    text += "\nCERTIFICATIONS\n";
    resume.certifications.forEach((cert) => {
      text += `${cert.title} - ${cert.date}\n`;
    });
  }

  return text;
}

