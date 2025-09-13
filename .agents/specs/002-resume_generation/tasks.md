# Phase 1: Dependencies and Foundation
- [x] Add jinja2>=3.1.0 dependency to pyproject.toml for HTML template rendering
- [x] Add PyPDF2>=3.0.0 dependency to pyproject.toml for PDF reading capabilities
- [x] Add weasyprint>=60.0 dependency to pyproject.toml for HTML to PDF conversion
- [x] Add typer>=0.9.0 dependency to pyproject.toml for CLI functionality
- [x] Add streamlit-pdf-viewer>=0.1.0 dependency to pyproject.toml for PDF display
- [x] Create data/resumes directory for PDF file storage

# Phase 2: Database Schema Implementation
- [x] Create Job model in src/database.py with all required fields (id, user_id, job_description, company_name, job_title, resume_filename, created_at, updated_at)
- [x] Add foreign key relationship from Job.user_id to User.id
- [x] Update database initialization to create Job table
- [x] Add Job model to DatabaseManager class methods
- [x] Add CRUD methods for Job model (create, get_by_id, list_by_user_id, update, delete)

# Phase 3: Data Adapter Updates
- [x] Fix import paths in src/features/resume/data_adapter.py (change src.db.* to src.*)
- [x] Remove references to non-existent models (CandidateResponse, Certification)
- [x] Update fetch_user_data() function to match current database schema
- [x] Update transform_user_to_resume_data() to map current schema fields to ResumeData format
- [x] Remove certification data handling (not in current schema)

# Phase 4: Agent State and Workflow Updates
- [x] Update InputState in src/agents/main/state.py to include user information fields (user_name, user_email, user_phone, user_linkedin_url, user_education)
- [x] Update generate_resume function in src/generate_resume.py to pass user information to agent
- [x] Update ResumeService.generate_resume() to fetch and pass user data to agent workflow
- [x] Ensure user information flows correctly through the agent pipeline

# Phase 5: PDF Generation Implementation
- [x] Overhaul create_resume node in src/agents/main/nodes/create_resume.py to generate PDFs instead of strings
- [x] Implement HTML template rendering using jinja2 and resume_001.html template
- [x] Implement HTML to PDF conversion using weasyprint
- [x] Add UUID generation for PDF filenames
- [x] Implement PDF file saving to data/resumes/ directory
- [x] Update node to return filename instead of formatted string
- [x] Ensure intermediate HTML files are properly discarded

# Phase 6: Resume Service Updates
- [x] Update ResumeService.generate_resume() to handle PDF generation workflow
- [x] Modify service to create Job database record after PDF generation
- [x] Update service to return Job object instead of string
- [x] Add error handling for PDF generation failures
- [x] Add error handling for database transaction failures

# Phase 7: Jobs Page Implementation
- [x] Create app/pages/jobs.py with job index view
- [x] Implement table display of job applications with columns (Job Description, Company, Job Title, Created Date)
- [x] Add truncation for long job descriptions in table view
- [x] Implement sorting by creation date (newest first)
- [x] Add clickable rows to open job detail dialog
- [x] Create job detail dialog component with full job description and PDF display
- [x] Implement PDF display using st.pdf component with stretch=True
- [x] Add metadata display (created date, filename) in detail dialog

# Phase 8: Navigation and UI Updates
- [x] Update app/main.py to include Jobs page in navigation
- [x] Add Jobs page to navigation with appropriate icon (💼)
- [x] Update app/pages/home.py to display PDF resumes instead of text
- [x] Replace text area display with st.pdf component in home page
- [x] Add success message with link to Jobs page after resume generation
- [x] Handle error states when no PDF is generated
- [x] Ensure PDF display works correctly in all contexts
