/**
 * Utility functions for formatting experiences with achievements.
 * Based on the Python formatter in apps/api/src/shared/formatters.py
 */

import type { Experience, Achievement } from "@resume/database/types";

/**
 * Format a single experience with its achievements into a standardized string.
 */
export function formatExperienceWithAchievements(
  experience: Experience,
  achievements: Achievement[]
): string {
  // Format dates
  const startDate = experience.start_date
    ? new Date(experience.start_date).toLocaleDateString("en-US", {
        month: "short",
        year: "numeric",
      })
    : "";
  const endDate = experience.end_date
    ? new Date(experience.end_date).toLocaleDateString("en-US", {
        month: "short",
        year: "numeric",
      })
    : "Present";

  const lines: string[] = [
    `# ${experience.company_name}`,
    `ID: ${experience.id}`,
    `Title: ${experience.job_title}`,
  ];

  // Add optional location
  if (experience.location) {
    lines.push(`Location: ${experience.location}`);
  }

  lines.push(`Duration: ${startDate} - ${endDate}`);
  lines.push(""); // Blank line

  // Add optional company overview
  if (experience.company_overview) {
    lines.push("## Company Overview");
    lines.push(experience.company_overview);
    lines.push("");
  }

  // Add optional role overview
  if (experience.role_overview) {
    lines.push("## Role Overview");
    lines.push(experience.role_overview);
    lines.push("");
  }

  // Add optional skills (skills is stored as Json in DB, should be string[])
  const skills = experience.skills as string[] | null;
  if (skills && Array.isArray(skills) && skills.length > 0) {
    lines.push("## Skills");
    for (const skill of skills) {
      lines.push(`- ${skill}`);
    }
    lines.push("");
  }

  // Add achievements section
  if (achievements && achievements.length > 0) {
    lines.push("## Achievements");
    lines.push("");
    for (const achievement of achievements) {
      lines.push(`### ${achievement.title}`);
      lines.push(`ID: ${achievement.id}`);
      lines.push(achievement.content);
      lines.push("");
    }
  }

  return lines.join("\n");
}

/**
 * Format all experiences into a single string with clear separation.
 */
export function formatAllExperiences(
  experiences: Experience[],
  achievementsByExp: Map<number, Achievement[]> = new Map()
): string {
  if (!experiences || experiences.length === 0) {
    return "No work experience available.";
  }

  const formattedSections = experiences.map((exp) => {
    const achievements = achievementsByExp.get(exp.id) || [];
    return formatExperienceWithAchievements(exp, achievements);
  });

  const divider = "\n" + "=".repeat(80) + "\n\n";
  return formattedSections.join(divider);
}

