/**
 * Database type exports and convenience aliases.
 *
 * Usage:
 *   import type { Job, JobInsert, Experience } from "@resume/database/types";
 */

export type { Database } from "./database.types";

// Import Database type for convenience aliases
import type { Database } from "./database.types";

// Helper type for accessing table types
type Tables = Database["public"]["Tables"];

// =============================================================================
// Users
// =============================================================================
export type User = Tables["users"]["Row"];
export type UserInsert = Tables["users"]["Insert"];
export type UserUpdate = Tables["users"]["Update"];

// =============================================================================
// Experiences
// =============================================================================
export type Experience = Tables["experiences"]["Row"];
export type ExperienceInsert = Tables["experiences"]["Insert"];
export type ExperienceUpdate = Tables["experiences"]["Update"];

// =============================================================================
// Achievements
// =============================================================================
export type Achievement = Tables["achievements"]["Row"];
export type AchievementInsert = Tables["achievements"]["Insert"];
export type AchievementUpdate = Tables["achievements"]["Update"];

// =============================================================================
// Education
// =============================================================================
export type Education = Tables["education"]["Row"];
export type EducationInsert = Tables["education"]["Insert"];
export type EducationUpdate = Tables["education"]["Update"];

// =============================================================================
// Certifications
// =============================================================================
export type Certification = Tables["certifications"]["Row"];
export type CertificationInsert = Tables["certifications"]["Insert"];
export type CertificationUpdate = Tables["certifications"]["Update"];

// =============================================================================
// Jobs
// =============================================================================
export type Job = Tables["jobs"]["Row"];
export type JobInsert = Tables["jobs"]["Insert"];
export type JobUpdate = Tables["jobs"]["Update"];

// =============================================================================
// Resumes
// =============================================================================
export type Resume = Tables["resumes"]["Row"];
export type ResumeInsert = Tables["resumes"]["Insert"];
export type ResumeUpdate = Tables["resumes"]["Update"];

// =============================================================================
// Resume Versions
// =============================================================================
export type ResumeVersion = Tables["resume_versions"]["Row"];
export type ResumeVersionInsert = Tables["resume_versions"]["Insert"];
export type ResumeVersionUpdate = Tables["resume_versions"]["Update"];

// =============================================================================
// Cover Letters
// =============================================================================
export type CoverLetter = Tables["cover_letters"]["Row"];
export type CoverLetterInsert = Tables["cover_letters"]["Insert"];
export type CoverLetterUpdate = Tables["cover_letters"]["Update"];

// =============================================================================
// Cover Letter Versions
// =============================================================================
export type CoverLetterVersion = Tables["cover_letter_versions"]["Row"];
export type CoverLetterVersionInsert = Tables["cover_letter_versions"]["Insert"];
export type CoverLetterVersionUpdate = Tables["cover_letter_versions"]["Update"];

// =============================================================================
// Messages
// =============================================================================
export type Message = Tables["messages"]["Row"];
export type MessageInsert = Tables["messages"]["Insert"];
export type MessageUpdate = Tables["messages"]["Update"];

// =============================================================================
// Responses
// =============================================================================
export type Response = Tables["responses"]["Row"];
export type ResponseInsert = Tables["responses"]["Insert"];
export type ResponseUpdate = Tables["responses"]["Update"];

// =============================================================================
// Notes
// =============================================================================
export type Note = Tables["notes"]["Row"];
export type NoteInsert = Tables["notes"]["Insert"];
export type NoteUpdate = Tables["notes"]["Update"];

// =============================================================================
// Job Intake Sessions
// =============================================================================
export type JobIntakeSession = Tables["job_intake_sessions"]["Row"];
export type JobIntakeSessionInsert = Tables["job_intake_sessions"]["Insert"];
export type JobIntakeSessionUpdate = Tables["job_intake_sessions"]["Update"];

// =============================================================================
// Job Intake Chat Messages
// =============================================================================
export type JobIntakeChatMessage = Tables["job_intake_chat_messages"]["Row"];
export type JobIntakeChatMessageInsert = Tables["job_intake_chat_messages"]["Insert"];
export type JobIntakeChatMessageUpdate = Tables["job_intake_chat_messages"]["Update"];

// =============================================================================
// Experience Proposals
// =============================================================================
export type ExperienceProposal = Tables["experience_proposals"]["Row"];
export type ExperienceProposalInsert = Tables["experience_proposals"]["Insert"];
export type ExperienceProposalUpdate = Tables["experience_proposals"]["Update"];

// =============================================================================
// Templates
// =============================================================================
export type Template = Tables["templates"]["Row"];
export type TemplateInsert = Tables["templates"]["Insert"];
export type TemplateUpdate = Tables["templates"]["Update"];

// =============================================================================
// Enum Types
// =============================================================================
export type JobStatus = Database["public"]["Enums"]["job_status"];
export type MessageChannel = Database["public"]["Enums"]["message_channel"];
export type ResponseSource = Database["public"]["Enums"]["response_source"];
export type ProposalType = Database["public"]["Enums"]["proposal_type"];
export type ProposalStatus = Database["public"]["Enums"]["proposal_status"];
export type ResumeVersionEvent = Database["public"]["Enums"]["resume_version_event"];
export type TemplateType = Database["public"]["Enums"]["template_type"];

// =============================================================================
// Resume JSON Data Types
// =============================================================================
// These types represent the JSON structure stored in resume_json columns.
// They match the format used by both the Python agents and the frontend.

/**
 * An experience entry within a resume JSON.
 * Contains a reference to the source experience and tailored content.
 */
export interface ResumeExperience {
  /** Reference to the experience record ID */
  experience_id?: number;
  /** Internal ID for UI tracking */
  id?: number;
  /** Job title, potentially tailored for this resume */
  title?: string;
  /** Company name */
  company?: string;
  /** Employment start date */
  start_date?: string;
  /** Employment end date (null for current positions) */
  end_date?: string | null;
  /** Location of the position */
  location?: string;
  /** Bullet points/achievements for this experience, tailored to the job */
  points?: string[];
}

/**
 * An education entry within a resume JSON.
 */
export interface ResumeEducation {
  /** Reference to the education record ID */
  education_id?: number;
  /** Internal ID for UI tracking */
  id?: number;
  /** Name of the educational institution */
  institution?: string;
  /** Degree type (e.g., "Bachelor of Science") */
  degree?: string;
  /** Field of study/major */
  major?: string;
  /** Graduation date */
  grad_date?: string;
  /** GPA (optional) */
  gpa?: string | null;
}

/**
 * A certification entry within a resume JSON.
 */
export interface ResumeCertification {
  /** Reference to the certification record ID */
  certification_id?: number;
  /** Internal ID for UI tracking */
  id?: number;
  /** Certification title/name */
  title?: string;
  /** Issuing organization */
  issuing_organization?: string;
  /** Date issued or obtained */
  date?: string;
  /** Expiration date (if applicable) */
  expiration_date?: string | null;
}

/**
 * The complete resume JSON structure stored in the database.
 * This is the schema for the `resume_json` column in resumes and resume_versions tables.
 */
export interface ResumeData {
  /** Full name */
  name?: string;
  /** Professional title/headline */
  title?: string;
  /** Email address */
  email?: string;
  /** Phone number */
  phone?: string;
  /** Location (city, state, etc.) */
  location?: string;
  /** LinkedIn profile URL */
  linkedin_url?: string;
  /** Professional summary tailored to the job */
  professional_summary?: string;
  /** List of skills relevant to the position */
  skills?: string[];
  /** Work experience entries */
  experience?: ResumeExperience[];
  /** Education entries */
  education?: ResumeEducation[];
  /** Certification entries */
  certifications?: ResumeCertification[];
  /** IDs of education records to include (used during generation) */
  education_ids?: number[];
  /** IDs of certification records to include (used during generation) */
  certification_ids?: number[];
  /** Allow additional properties for flexibility */
  [key: string]: unknown;
}

