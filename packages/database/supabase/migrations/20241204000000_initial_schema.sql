-- =============================================================================
-- Initial Schema Migration: SQLite to PostgreSQL
-- =============================================================================
-- This migration creates all tables required for the Resume application,
-- migrated from SQLite to PostgreSQL with proper data types and constraints.
-- =============================================================================

-- =============================================================================
-- ENUM Types
-- =============================================================================

-- Job application status
CREATE TYPE job_status AS ENUM (
  'Saved',
  'Applied',
  'Interviewing',
  'Not Selected',
  'No Offer',
  'Hired'
);

-- Message channel types
CREATE TYPE message_channel AS ENUM (
  'email',
  'linkedin'
);

-- Response source types
CREATE TYPE response_source AS ENUM (
  'manual',
  'application'
);

-- Experience proposal types
CREATE TYPE proposal_type AS ENUM (
  'achievement_add',
  'achievement_update',
  'achievement_delete',
  'skill_add',
  'skill_delete',
  'role_overview_update',
  'company_overview_update'
);

-- Proposal status
CREATE TYPE proposal_status AS ENUM (
  'pending',
  'accepted',
  'rejected'
);

-- Resume version event types
CREATE TYPE resume_version_event AS ENUM (
  'generate',
  'save',
  'reset'
);

-- Template types
CREATE TYPE template_type AS ENUM (
  'resume',
  'cover_letter'
);

-- =============================================================================
-- Helper Function for updated_at Timestamps
-- =============================================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- =============================================================================
-- Users Table
-- =============================================================================

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  first_name TEXT NOT NULL,
  last_name TEXT NOT NULL,
  phone_number TEXT,
  email TEXT,
  address TEXT,
  city TEXT,
  state TEXT,
  zip_code TEXT,
  linkedin_url TEXT,
  github_url TEXT,
  website_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TRIGGER update_users_updated_at
  BEFORE UPDATE ON users
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Experiences Table
-- =============================================================================

CREATE TABLE experiences (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  company_name TEXT NOT NULL,
  job_title TEXT NOT NULL,
  location TEXT,
  start_date DATE NOT NULL,
  end_date DATE,
  company_overview TEXT,
  role_overview TEXT,
  skills JSONB NOT NULL DEFAULT '[]',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_experiences_user_id ON experiences(user_id);
CREATE INDEX idx_experiences_start_date ON experiences(start_date DESC);

CREATE TRIGGER update_experiences_updated_at
  BEFORE UPDATE ON experiences
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Achievements Table
-- =============================================================================

CREATE TABLE achievements (
  id SERIAL PRIMARY KEY,
  experience_id INTEGER NOT NULL REFERENCES experiences(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  content TEXT NOT NULL,
  "order" INTEGER NOT NULL DEFAULT 0,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_achievements_experience_id ON achievements(experience_id);
CREATE INDEX idx_achievements_order ON achievements(experience_id, "order");

CREATE TRIGGER update_achievements_updated_at
  BEFORE UPDATE ON achievements
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Education Table
-- =============================================================================

CREATE TABLE education (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  institution TEXT NOT NULL,
  degree TEXT NOT NULL,
  major TEXT NOT NULL,
  grad_date DATE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_education_user_id ON education(user_id);
CREATE INDEX idx_education_grad_date ON education(grad_date DESC);

CREATE TRIGGER update_education_updated_at
  BEFORE UPDATE ON education
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Certifications Table
-- =============================================================================

CREATE TABLE certifications (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  title TEXT NOT NULL,
  institution TEXT,
  date DATE NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_certifications_user_id ON certifications(user_id);
CREATE INDEX idx_certifications_date ON certifications(date DESC);

CREATE TRIGGER update_certifications_updated_at
  BEFORE UPDATE ON certifications
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Jobs Table
-- =============================================================================

CREATE TABLE jobs (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  job_description TEXT NOT NULL,
  company_name TEXT,
  job_title TEXT,
  status job_status NOT NULL DEFAULT 'Saved',
  is_favorite BOOLEAN NOT NULL DEFAULT FALSE,
  applied_at TIMESTAMPTZ,
  has_resume BOOLEAN NOT NULL DEFAULT FALSE,
  has_cover_letter BOOLEAN NOT NULL DEFAULT FALSE,
  resume_chat_thread_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_jobs_user_id ON jobs(user_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_is_favorite ON jobs(is_favorite) WHERE is_favorite = TRUE;
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);

CREATE TRIGGER update_jobs_updated_at
  BEFORE UPDATE ON jobs
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Resume Versions Table
-- =============================================================================
-- Consolidated table for all resume versions. The pinned version represents
-- the "current" resume for a job. No separate resumes table needed.
-- =============================================================================

CREATE TABLE resume_versions (
  id SERIAL PRIMARY KEY,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  version_index INTEGER NOT NULL,
  parent_version_id INTEGER,
  event_type resume_version_event NOT NULL,
  template_name TEXT NOT NULL,
  resume_json TEXT NOT NULL,
  is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
  locked BOOLEAN NOT NULL DEFAULT FALSE,
  created_by_user_id INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_resume_version_job_id_version_index UNIQUE (job_id, version_index)
);

CREATE INDEX idx_resume_versions_job_id ON resume_versions(job_id);
CREATE INDEX idx_resume_versions_job_id_created_at_desc ON resume_versions(job_id, created_at DESC);

-- Ensure only one pinned version per job
CREATE UNIQUE INDEX idx_resume_versions_pinned ON resume_versions(job_id) WHERE is_pinned = TRUE;

-- =============================================================================
-- Cover Letter Versions Table
-- =============================================================================
-- Consolidated table for all cover letter versions. The pinned version represents
-- the "current" cover letter for a job. No separate cover_letters table needed.
-- =============================================================================

CREATE TABLE cover_letter_versions (
  id SERIAL PRIMARY KEY,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  version_index INTEGER NOT NULL,
  parent_version_id INTEGER,
  event_type resume_version_event NOT NULL,
  template_name TEXT NOT NULL,
  cover_letter_json TEXT NOT NULL,
  is_pinned BOOLEAN NOT NULL DEFAULT FALSE,
  locked BOOLEAN NOT NULL DEFAULT FALSE,
  created_by_user_id INTEGER NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_cover_letter_version_job_id_version_index UNIQUE (job_id, version_index)
);

CREATE INDEX idx_cover_letter_versions_job_id ON cover_letter_versions(job_id);
CREATE INDEX idx_cover_letter_versions_job_id_created_at_desc ON cover_letter_versions(job_id, created_at DESC);

-- Ensure only one pinned version per job
CREATE UNIQUE INDEX idx_cover_letter_versions_pinned ON cover_letter_versions(job_id) WHERE is_pinned = TRUE;

-- =============================================================================
-- Messages Table
-- =============================================================================

CREATE TABLE messages (
  id SERIAL PRIMARY KEY,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  channel message_channel NOT NULL,
  body TEXT NOT NULL,
  sent_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_job_id ON messages(job_id);

CREATE TRIGGER update_messages_updated_at
  BEFORE UPDATE ON messages
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Responses Table
-- =============================================================================

CREATE TABLE responses (
  id SERIAL PRIMARY KEY,
  job_id INTEGER REFERENCES jobs(id) ON DELETE CASCADE,
  prompt TEXT NOT NULL,
  response TEXT NOT NULL,
  source response_source NOT NULL,
  ignore BOOLEAN NOT NULL DEFAULT FALSE,
  locked BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_responses_job_id ON responses(job_id);
CREATE INDEX idx_responses_source ON responses(source);
CREATE INDEX idx_responses_ignore ON responses(ignore);
CREATE INDEX idx_responses_created_at ON responses(created_at DESC);

CREATE TRIGGER update_responses_updated_at
  BEFORE UPDATE ON responses
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Notes Table
-- =============================================================================

CREATE TABLE notes (
  id SERIAL PRIMARY KEY,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_notes_job_id ON notes(job_id);

CREATE TRIGGER update_notes_updated_at
  BEFORE UPDATE ON notes
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Job Intake Sessions Table
-- =============================================================================

CREATE TABLE job_intake_sessions (
  id SERIAL PRIMARY KEY,
  job_id INTEGER NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
  current_step INTEGER NOT NULL,
  step1_completed BOOLEAN NOT NULL DEFAULT FALSE,
  step2_completed BOOLEAN NOT NULL DEFAULT FALSE,
  step3_completed BOOLEAN NOT NULL DEFAULT FALSE,
  gap_analysis TEXT,
  stakeholder_analysis TEXT,
  resume_chat_thread_id TEXT,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT uq_job_intake_session_job_id UNIQUE (job_id),
  CONSTRAINT chk_current_step CHECK (current_step >= 1 AND current_step <= 3)
);

CREATE INDEX idx_job_intake_sessions_job_id ON job_intake_sessions(job_id);

CREATE TRIGGER update_job_intake_sessions_updated_at
  BEFORE UPDATE ON job_intake_sessions
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Job Intake Chat Messages Table
-- =============================================================================

CREATE TABLE job_intake_chat_messages (
  id SERIAL PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES job_intake_sessions(id) ON DELETE CASCADE,
  step INTEGER NOT NULL,
  messages JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT chk_step CHECK (step >= 1 AND step <= 3)
);

CREATE INDEX idx_job_intake_chat_messages_session_id ON job_intake_chat_messages(session_id);
CREATE INDEX idx_job_intake_chat_messages_session_step ON job_intake_chat_messages(session_id, step);

-- =============================================================================
-- Experience Proposals Table
-- =============================================================================

CREATE TABLE experience_proposals (
  id SERIAL PRIMARY KEY,
  session_id INTEGER NOT NULL REFERENCES job_intake_sessions(id) ON DELETE CASCADE,
  proposal_type proposal_type NOT NULL,
  experience_id INTEGER NOT NULL REFERENCES experiences(id) ON DELETE CASCADE,
  achievement_id INTEGER REFERENCES achievements(id) ON DELETE SET NULL,
  proposed_content JSONB NOT NULL,
  original_proposed_content JSONB NOT NULL,
  status proposal_status NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_experience_proposals_session_id ON experience_proposals(session_id);
CREATE INDEX idx_experience_proposals_experience_id ON experience_proposals(experience_id);
CREATE INDEX idx_experience_proposals_status ON experience_proposals(status);

CREATE TRIGGER update_experience_proposals_updated_at
  BEFORE UPDATE ON experience_proposals
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Templates Table
-- =============================================================================

CREATE TABLE templates (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  type template_type NOT NULL,
  html_content TEXT NOT NULL,
  description TEXT,
  preview_image_url TEXT,
  is_default BOOLEAN NOT NULL DEFAULT FALSE,
  metadata JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_templates_type ON templates(type);
CREATE INDEX idx_templates_is_default ON templates(is_default) WHERE is_default = TRUE;

CREATE TRIGGER update_templates_updated_at
  BEFORE UPDATE ON templates
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- Comments for Documentation
-- =============================================================================

COMMENT ON TABLE users IS 'User profiles with contact information';
COMMENT ON TABLE experiences IS 'Work experience entries for users';
COMMENT ON TABLE achievements IS 'Achievements/accomplishments linked to work experiences';
COMMENT ON TABLE education IS 'Education history for users';
COMMENT ON TABLE certifications IS 'Professional certifications for users';
COMMENT ON TABLE jobs IS 'Job applications being tracked';
COMMENT ON TABLE resume_versions IS 'All resume versions for jobs. The pinned version (is_pinned=true) is the current resume.';
COMMENT ON TABLE cover_letter_versions IS 'All cover letter versions for jobs. The pinned version (is_pinned=true) is the current cover letter.';
COMMENT ON TABLE messages IS 'Outreach messages (email/LinkedIn) for jobs';
COMMENT ON TABLE responses IS 'Saved responses for common application questions';
COMMENT ON TABLE notes IS 'User notes attached to job applications';
COMMENT ON TABLE job_intake_sessions IS 'Tracks state of job intake workflow';
COMMENT ON TABLE job_intake_chat_messages IS 'Chat history for intake flow conversations';
COMMENT ON TABLE experience_proposals IS 'AI-generated proposals for updating experiences';
COMMENT ON TABLE templates IS 'HTML templates for resumes and cover letters';

COMMENT ON COLUMN experiences.skills IS 'Array of skill strings stored as JSONB';
COMMENT ON COLUMN job_intake_sessions.resume_chat_thread_id IS 'LangGraph thread ID for resume chat session';
COMMENT ON COLUMN job_intake_chat_messages.messages IS 'JSON array of LangChain message format';
COMMENT ON COLUMN experience_proposals.proposed_content IS 'JSON containing the proposal data';
COMMENT ON COLUMN experience_proposals.original_proposed_content IS 'Original AI-generated proposal for revert';
COMMENT ON COLUMN templates.metadata IS 'Additional template configuration as JSON';
COMMENT ON COLUMN resume_versions.is_pinned IS 'When true, this version is the current resume for the job';
COMMENT ON COLUMN cover_letter_versions.is_pinned IS 'When true, this version is the current cover letter for the job';

