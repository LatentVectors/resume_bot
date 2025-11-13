# Spec Tasks

## Tasks

- [x] 1. Move shared exceptions and update dependencies

  - [x] 1.1 Create `src/exceptions.py` and move `OpenAIQuotaExceededError` from `app/exceptions.py`
  - [x] 1.2 Update `app/exceptions.py` to import from `src.exceptions` (maintain backward compatibility temporarily)
  - [x] 1.3 Update `app/services/job_intake_service/workflows/gap_analysis.py` to import from `src.exceptions`
  - [x] 1.4 Add FastAPI dependencies to `pyproject.toml`: `fastapi>=0.109.0`, `uvicorn[standard]>=0.27.0`, `httpx>=0.26.0`
  - [x] 1.5 Update `src/config.py` to add API configuration fields: `api_host`, `api_port`, `api_reload`, `cors_origins`

- [x] 2. Create FastAPI application infrastructure

  - [x] 2.1 Create `api/main.py` with FastAPI app initialization, CORS middleware, and global exception handler
  - [x] 2.2 Create `api/dependencies.py` with `get_session()` dependency for database sessions
  - [x] 2.3 Create `api/utils/errors.py` with error classes: `NotFoundError`, `ValidationError`, `QuotaExceededError`
  - [x] 2.4 Create `api/config.py` for API-specific configuration (if needed, otherwise use `src/config`)
  - [x] 2.5 Create `api/middleware.py` for logging middleware (optional, can be in main.py)

- [x] 3. Create Pydantic schemas for Users and Jobs

  - [x] 3.1 Create `api/schemas/__init__.py`
  - [x] 3.2 Create `api/schemas/user.py` with `UserCreate`, `UserUpdate`, `UserResponse` models
  - [x] 3.3 Create `api/schemas/job.py` with `JobCreate`, `JobUpdate`, `JobResponse` models
  - [x] 3.4 Ensure all schemas use `from_attributes = True` for SQLModel conversion
  - [x] 3.5 Add Field validations and descriptions to all schema fields

- [x] 4. Create Pydantic schemas for Experiences, Education, and Certificates

  - [x] 4.1 Create `api/schemas/experience.py` with models for Experience, Achievement, and Proposal schemas
  - [x] 4.2 Create `api/schemas/education.py` with `EducationCreate`, `EducationUpdate`, `EducationResponse` models
  - [x] 4.3 Create `api/schemas/certificate.py` with `CertificateCreate`, `CertificateUpdate`, `CertificateResponse` models
  - [x] 4.4 Ensure all schemas properly handle optional fields and relationships

- [x] 5. Create Pydantic schemas for Resumes, Cover Letters, and Templates

  - [x] 5.1 Create `api/schemas/resume.py` with `ResumeVersionResponse`, `ResumeCreate`, and related models
  - [x] 5.2 Create `api/schemas/cover_letter.py` with `CoverLetterVersionResponse`, `CoverLetterCreate`, and related models
  - [x] 5.3 Create `api/schemas/template.py` with template listing and detail models
  - [x] 5.4 Ensure resume and cover letter schemas handle versioning properly

- [x] 6. Create Pydantic schemas for Messages, Responses, and Workflows

  - [x] 6.1 Create `api/schemas/message.py` with `MessageCreate`, `MessageResponse` models
  - [x] 6.2 Create `api/schemas/response.py` with `ResponseCreate`, `ResponseUpdate`, `ResponseResponse` models
  - [x] 6.3 Create `api/schemas/workflow.py` with request/response models for all workflow endpoints
  - [x] 6.4 Ensure workflow schemas match the expected inputs/outputs from existing workflow functions

- [x] 7. Move and refactor User and Job services to API

  - [x] 7.1 Copy `app/services/user_service.py` to `api/services/user_service.py`
  - [x] 7.2 Copy `app/services/job_service.py` to `api/services/job_service.py`
  - [x] 7.3 Remove Streamlit dependencies (st.session_state, st.error) from both services
  - [x] 7.4 Update `JobService.save_job()` to accept `user_id` parameter instead of getting from session
  - [x] 7.5 Update all imports to use `src.database` and `src.exceptions` instead of `app` imports
  - [x] 7.6 Ensure services return SQLModel objects, not UI-specific data

- [x] 8. Move and refactor Experience, Education, and Certificate services to API

  - [x] 8.1 Copy `app/services/experience_service.py` to `api/services/experience_service.py`
  - [x] 8.2 Copy `app/services/education_service.py` to `api/services/education_service.py`
  - [x] 8.3 Copy `app/services/certificate_service.py` to `api/services/certificate_service.py`
  - [x] 8.4 Remove Streamlit dependencies from all three services
  - [x] 8.5 Update imports to use `src.database` and `src.exceptions`
  - [x] 8.6 Ensure all service methods accept explicit parameters (no session state access)

- [x] 9. Move and refactor Resume and Cover Letter services to API

  - [x] 9.1 Copy `app/services/resume_service.py` to `api/services/resume_service.py`
  - [x] 9.2 Copy `app/services/cover_letter_service.py` to `api/services/cover_letter_service.py`
  - [x] 9.3 Copy `app/services/render_pdf.py` to `api/services/pdf_service.py` and rename class
  - [x] 9.4 Remove Streamlit dependencies (st.session_state, st.download_button, etc.)
  - [x] 9.5 Update imports to use `src.database` and `src.exceptions`
  - [x] 9.6 Ensure PDF generation returns bytes, not Streamlit download widgets

- [x] 10. Move Template, Chat Message, and Response services to API

  - [x] 10.1 Copy `app/services/template_service.py` to `api/services/template_service.py`
  - [x] 10.2 Copy `app/services/chat_message_service.py` to `api/services/chat_message_service.py`
  - [x] 10.3 Create `api/services/response_service.py` (if it exists in app/services, copy it)
  - [x] 10.4 Remove Streamlit dependencies from all services
  - [x] 10.5 Update imports to use `src.database` and `src.exceptions`

- [x] 11. Move Job Intake Service and Workflows to API

  - [x] 11.1 Copy `app/services/job_intake_service/service.py` to `api/services/job_intake_service/service.py`
  - [x] 11.2 Copy all workflow files from `app/services/job_intake_service/workflows/` to `api/services/job_intake_service/workflows/`
  - [x] 11.3 Update all workflow imports to use `src.exceptions` instead of `app.exceptions`
  - [x] 11.4 Remove Streamlit dependencies from `JobIntakeService` and workflows
  - [x] 11.5 Update `JobIntakeService` methods to accept explicit parameters instead of using session state
  - [x] 11.6 Ensure workflows return data structures, not UI components

- [x] 12. Create User and Job API routes

  - [x] 12.1 Create `api/routes/__init__.py`
  - [x] 12.2 Create `api/routes/users.py` with CRUD endpoints: GET /users, GET /users/{id}, POST /users, PATCH /users/{id}, DELETE /users/{id}, GET /users/current
  - [x] 12.3 Create `api/routes/jobs.py` with CRUD endpoints and job-specific endpoints (favorite, status, apply, intake-session)
  - [x] 12.4 Use dependency injection for database sessions in all routes
  - [x] 12.5 Add request validation using Pydantic schemas and response serialization
  - [x] 12.6 Implement proper error handling using `api/utils/errors.py` classes
  - [x] 12.7 Register routes in `api/main.py` with prefix `/api/v1`

- [x] 13. Create Experience, Education, and Certificate API routes

  - [x] 13.1 Create `api/routes/experiences.py` with CRUD endpoints for experiences and achievements
  - [x] 13.2 Create `api/routes/experiences.py` with proposal endpoints (list, create, accept, reject, delete)
  - [x] 13.3 Create `api/routes/education.py` with CRUD endpoints
  - [x] 13.4 Create `api/routes/certificates.py` with CRUD endpoints
  - [x] 13.5 Use dependency injection, Pydantic validation, and error handling
  - [x] 13.6 Register routes in `api/main.py`

- [x] 14. Create Resume and Cover Letter API routes

  - [x] 14.1 Create `api/routes/resumes.py` with version management endpoints (list, get, create, pin, compare)
  - [x] 14.2 Create `api/routes/resumes.py` with PDF endpoints (download, preview)
  - [x] 14.3 Create `api/routes/cover_letters.py` with version management and PDF endpoints
  - [x] 14.4 Ensure PDF endpoints return proper FastAPI FileResponse or StreamingResponse
  - [x] 14.5 Use dependency injection, Pydantic validation, and error handling
  - [x] 14.6 Register routes in `api/main.py`

- [x] 15. Create Template, Message, and Response API routes

  - [x] 15.1 Create `api/routes/templates.py` with endpoints for listing and getting resume/cover letter templates
  - [x] 15.2 Create `api/routes/messages.py` with CRUD endpoints for chat messages
  - [x] 15.3 Create `api/routes/responses.py` with CRUD endpoints for interview responses
  - [x] 15.4 Use dependency injection, Pydantic validation, and error handling
  - [x] 15.5 Register routes in `api/main.py`

- [x] 16. Create Workflow API routes

  - [x] 16.1 Create `api/routes/workflows.py` with endpoint for gap analysis: POST /workflows/gap-analysis
  - [x] 16.2 Add endpoint for stakeholder analysis: POST /workflows/stakeholder-analysis
  - [x] 16.3 Add endpoint for experience extraction: POST /workflows/experience-extraction
  - [x] 16.4 Add endpoint for resume chat: POST /workflows/resume-chat
  - [x] 16.5 Add endpoint for resume generation (LangGraph agent): POST /workflows/resume-generation
  - [x] 16.6 Use Pydantic request/response models from `api/schemas/workflow.py`
  - [x] 16.7 Handle `OpenAIQuotaExceededError` and convert to `QuotaExceededError` HTTP exception
  - [x] 16.8 Register routes in `api/main.py`

- [x] 17. Create API client base infrastructure

  - [x] 17.1 Create `app/api_client/__init__.py`
  - [x] 17.2 Create `app/api_client/client.py` with `APIClient` class supporting typed responses
  - [x] 17.3 Implement `_request()` method with `response_model` parameter for Pydantic validation
  - [x] 17.4 Implement `get()`, `post()`, `patch()`, `delete()` methods with type hints
  - [x] 17.5 Add error handling for HTTP errors and validation errors
  - [x] 17.6 Create global `api_client` instance

- [x] 18. Create API client endpoints for Users and Jobs

  - [x] 18.1 Create `app/api_client/endpoints/__init__.py`
  - [x] 18.2 Create `app/api_client/endpoints/users.py` with `UsersAPI` class
  - [x] 18.3 Implement all user endpoints returning typed `UserResponse` models
  - [x] 18.4 Create `app/api_client/endpoints/jobs.py` with `JobsAPI` class
  - [x] 18.5 Implement all job endpoints returning typed `JobResponse` models
  - [x] 18.6 Use Pydantic models from `api.schemas` for request/response types
  - [x] 18.7 Ensure all methods have proper type hints (e.g., `-> list[JobResponse]`)

- [x] 19. Create API client endpoints for Experiences, Education, and Certificates

  - [x] 19.1 Create `app/api_client/endpoints/experiences.py` with `ExperiencesAPI` class
  - [x] 19.2 Create `app/api_client/endpoints/education.py` with `EducationAPI` class
  - [x] 19.3 Create `app/api_client/endpoints/certificates.py` with `CertificatesAPI` class
  - [x] 19.4 Implement all CRUD endpoints with typed responses
  - [x] 19.5 Implement proposal endpoints in `ExperiencesAPI`
  - [x] 19.6 Use Pydantic models for all request/response types

- [x] 20. Create API client endpoints for Resumes, Cover Letters, and Templates

  - [x] 20.1 Create `app/api_client/endpoints/resumes.py` with `ResumesAPI` class
  - [x] 20.2 Create `app/api_client/endpoints/cover_letters.py` with `CoverLettersAPI` class
  - [x] 20.3 Create `app/api_client/endpoints/templates.py` with `TemplatesAPI` class
  - [x] 20.4 Implement all version management and PDF endpoints
  - [x] 20.5 Handle PDF responses appropriately (bytes or file downloads)
  - [x] 20.6 Use Pydantic models for all request/response types

- [x] 21. Create API client endpoints for Messages, Responses, and Workflows

  - [x] 21.1 Create `app/api_client/endpoints/messages.py` with `MessagesAPI` class
  - [x] 21.2 Create `app/api_client/endpoints/responses.py` with `ResponsesAPI` class
  - [x] 21.3 Create `app/api_client/endpoints/workflows.py` with `WorkflowsAPI` class
  - [x] 21.4 Implement all workflow endpoints with typed responses
  - [x] 21.5 Use Pydantic models for all request/response types

- [x] 22. Update User and Job pages to use API client

  - [x] 22.1 Update `app/pages/profile.py` to use `UsersAPI` instead of `UserService`
  - [x] 22.2 Update `app/pages/jobs.py` to use `JobsAPI` instead of `JobService`
  - [x] 22.3 Update `app/pages/job.py` to use `JobsAPI` instead of `JobService`
  - [x] 22.4 Replace direct service calls with async API client calls (use `asyncio.run()` or similar)
  - [x] 22.5 Update error handling to work with API responses
  - [x] 22.6 Ensure typed models are used (e.g., `list[JobResponse]` instead of `list[dict]`)

- [x] 23. Update Experience, Education, and Certificate dialogs to use API client

  - [x] 23.1 Update `app/dialog/experience_dialog.py` to use `ExperiencesAPI`
  - [x] 23.2 Update `app/dialog/education_dialog.py` to use `EducationAPI`
  - [x] 23.3 Update `app/dialog/certificate_dialog.py` to use `CertificatesAPI`
  - [x] 23.4 Update `app/dialog/resume_add_experience_dialog.py` to use `ExperiencesAPI` (not needed - uses in-memory drafts)
  - [x] 23.5 Update `app/dialog/resume_add_education_dialog.py` to use `EducationAPI` (not needed - uses in-memory drafts)
  - [x] 23.6 Update `app/dialog/resume_add_certificate_dialog.py` to use `CertificatesAPI` (not needed - uses in-memory drafts)
  - [x] 23.7 Replace service calls with API client calls and update error handling

- [x] 24. Update Job Intake flow to use API client

  - [x] 24.1 Update `app/dialog/job_intake_flow.py` to use `JobsAPI` for job operations
  - [x] 24.2 Update `app/dialog/job_intake/step1_details.py` to use `JobsAPI`
  - [x] 24.3 Update `app/dialog/job_intake/step2_experience_and_resume.py` to use `WorkflowsAPI` and `ResumesAPI`
  - [x] 24.4 Update `app/dialog/job_intake/step3_experience_proposals.py` to use `ExperiencesAPI`
  - [x] 24.5 Replace workflow calls with `WorkflowsAPI` endpoints
  - [x] 24.6 Update error handling for API responses

- [x] 25. Update Resume and Cover Letter pages to use API client

  - [x] 25.1 Update `app/pages/job_tabs/resume.py` to use `ResumesAPI` instead of `ResumeService`
  - [x] 25.2 Update `app/pages/job_tabs/cover.py` to use `CoverLettersAPI` instead of `CoverLetterService`
  - [x] 25.3 Replace PDF rendering calls with API client calls
  - [x] 25.4 Handle PDF responses (bytes) appropriately in Streamlit
  - [x] 25.5 Update version management UI to use API endpoints
  - [x] 25.6 Update error handling for API responses

- [x] 26. Update remaining pages and components to use API client

  - [x] 26.1 Update `app/pages/templates.py` to use `TemplatesAPI` (Note: templates.py uses TemplateService for LLM-based template generation, not CRUD operations. TemplatesAPI is for listing/getting existing templates. No API endpoint exists yet for template generation, so templates.py remains unchanged.)
  - [x] 26.2 Update `app/pages/responses.py` to use `ResponsesAPI`
  - [x] 26.3 Update `app/pages/job_tabs/messages.py` to use `MessagesAPI`
  - [x] 26.4 Update any remaining components that use services directly (Updated `app/components/copy_job_context_button.py`, `app/pages/home.py`, `app/main.py`)
  - [x] 26.5 Replace all service imports with API client imports
  - [x] 26.6 Update error handling throughout

- [ ] 27. Set up test infrastructure with database copying

  - [ ] 27.1 Create `tests/conftest.py` with `test_database_path` fixture that copies production database
  - [ ] 27.2 Create `test_session` fixture that uses copied database and rolls back after each test
  - [ ] 27.3 Use `monkeypatch` to temporarily override `settings.database_url` for tests
  - [ ] 27.4 Ensure test database is cleaned up after tests complete

- [ ] 28. Create minimal API tests

  - [ ] 28.1 Create `tests/api/__init__.py`
  - [ ] 28.2 Create `tests/api/test_jobs.py` with minimal tests: create job, get job, 404 handling
  - [ ] 28.3 Create `tests/api/test_workflows.py` with minimal test for one workflow endpoint
  - [ ] 28.4 Use `TestClient` from FastAPI and test fixtures from `conftest.py`
  - [ ] 28.5 Keep tests simple and focused on critical paths only

- [x] 29. Update application runner to start both API and Streamlit

  - [x] 29.1 Update `run.py` to import `uvicorn` and `multiprocessing`
  - [x] 29.2 Create `run_api()` function that starts FastAPI with uvicorn on port 8000
  - [x] 29.3 Create `run_streamlit()` function that starts Streamlit on port 8501
  - [x] 29.4 Update `main()` function to start API in separate process and Streamlit in main process
  - [x] 29.5 Add cleanup to terminate API process when Streamlit exits
  - [x] 29.6 Test that both services start correctly

- [x] 30. Final cleanup and validation
  - [x] 30.1 Verify all imports are updated (no `app` imports in `api/` directory)
  - [x] 30.2 Verify all API endpoints return typed Pydantic models
  - [x] 30.3 Verify all frontend code uses typed API client responses
  - [x] 30.4 Remove any remaining Streamlit dependencies from API services
  - [x] 30.5 Test that API starts and responds to health check endpoint
  - [x] 30.6 Verify CORS is configured correctly for Streamlit frontend
  - [ ] 30.7 Manual testing: verify all UI flows work with API backend
  - [ ] 30.8 Manual testing: verify LLM workflows function correctly through API
