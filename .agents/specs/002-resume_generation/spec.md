# Resume Generation with PDF Output - Implementation Specification

## Overview
Transform the current resume generation system from text-based output to PDF-based output using HTML templates. This includes creating a job tracking system, implementing PDF generation, and updating the UI to display PDF resumes.

## Goals
- Generate professional PDF resumes using HTML templates
- Track job applications and their associated resumes
- Display PDF resumes in the UI using Streamlit's PDF viewer
- Maintain extensibility for future features (cover letters, multiple templates, etc.)

---

## 1. Database Schema Changes

### 1.1 New Job Model
Create a new `Job` model to track job applications and their associated resumes:

```python
class Job(SQLModel, table=True):
    """Job application model for tracking resumes generated for specific jobs."""
    
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    job_description: str = Field(..., description="Original job description text")
    company_name: str | None = Field(default=None, description="Company name (for future use)")
    job_title: str | None = Field(default=None, description="Job title (for future use)")
    resume_filename: str = Field(..., description="UUID.pdf filename of generated resume")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

**Relationships:**
- One-to-many: User → Jobs (one user can have multiple job applications)
- Foreign key: `user_id` references `user.id`

### 1.2 Database Migration
- Update `src/database.py` to include the new Job model
- Ensure database initialization creates the new table
- No template field needed - template selection will be handled at generation time

---

## 2. Dependencies and Configuration

### 2.1 Required Dependencies
Add the following dependencies to `pyproject.toml`:

```toml
dependencies = [
    # ... existing dependencies ...
    "jinja2>=3.1.0",           # HTML template rendering
    "PyPDF2>=3.0.0",           # PDF reading capabilities
    "weasyprint>=60.0",        # HTML to PDF conversion
    "typer>=0.9.0",            # CLI functionality
    "streamlit-pdf-viewer>=0.1.0",  # PDF display in Streamlit
]
```

### 2.2 File Structure
- **PDF Storage**: Flat directory structure in `data/resumes/`
- **Filename Format**: `{UUID}.pdf` (e.g., `550e8400-e29b-41d4-a716-446655440000.pdf`)
- **No Subdirectories**: Keep structure simple for now (YAGNI principle)

---

## 3. Resume Generation System Updates

### 3.1 Agent Input State Enhancement
Update `src/agents/main/state.py` to include user information:

```python
class InputState(BaseModel):
    job_description: str
    experiences: list[Experience]
    responses: str
    # New fields for user information
    user_name: str  # Combined first_name + last_name
    user_email: str
    user_phone: str | None
    user_linkedin_url: str | None
    user_education: list[Education]  # From database Education model
```

### 3.2 Data Adapter Updates
Update `src/features/resume/data_adapter.py`:

**Current Issues to Fix:**
- Remove references to non-existent models (`CandidateResponse`, `Certification`)
- Update import paths from `src.db.*` to `src.*`
- Align with current database schema (User, Experience, Education models)

**Key Functions to Update:**
- `fetch_user_data()`: Return user, education data matching current schema
- `transform_user_to_resume_data()`: Map current schema fields to ResumeData format
- Remove references to certification data (not in current schema)

### 3.3 Create Resume Node Overhaul
Update `src/agents/main/nodes/create_resume.py`:

**Current Implementation:** Returns formatted string
**New Implementation:** Generate HTML template → Convert to PDF → Return filename

```python
def create_resume(state: InternalState) -> PartialInternalState:
    """
    Generate PDF resume from template and return filename.
    
    Process:
    1. Validate all required inputs
    2. Transform data to ResumeData format
    3. Render HTML template (resume_001.html)
    4. Convert HTML to PDF
    5. Save PDF to data/resumes/{UUID}.pdf
    6. Return filename for database storage
    """
```

**Template Selection:** Hardcode `"resume_001.html"` for now

### 3.4 Resume Service Updates
Update `app/services/resume_service.py`:

**Current Flow:** Generate text resume → Return string
**New Flow:** Generate PDF resume → Save to database → Return Job record

```python
class ResumeService:
    @staticmethod
    def generate_resume(
        job_description: str, 
        experiences: list[DbExperience], 
        responses: str = "", 
        user_id: int | None = None
    ) -> Job:
        """
        Generate PDF resume and create Job record.
        
        Returns:
            Job: Database record with resume filename
        """
```

**Key Changes:**
- Call updated agent workflow with user information
- Handle PDF filename generation (UUID)
- Create and save Job record to database
- Return Job object instead of string

---

## 4. User Interface Updates

### 4.1 Navigation Changes
Update `app/main.py` to include Jobs page:

```python
# Add to navigation
jobs_page = st.Page("pages/jobs.py", title="Jobs", icon="💼")
pg = st.navigation([home_page, user_page, jobs_page])
```

### 4.2 Jobs Page Implementation
Create `app/pages/jobs.py`:

**Features:**
- Table/index view of all job applications
- Columns: Job Description (truncated), Company, Job Title, Created Date
- Clickable rows to open detail dialog
- Sortable by creation date (newest first)

### 4.3 Job Detail Dialog
Create large dialog component for job details:

**Content:**
- Full job description text
- PDF resume display using `st.pdf` component
- Metadata: Created date, filename
- Close button

**PDF Display Configuration:**
```python
st.pdf(
    data=pdf_data, # Raw bytes data.
    height="stretch",
)
```

### 4.4 Home Page Updates
Update `app/pages/home.py`:

**Changes:**
- Replace text area display with PDF viewer
- Use `st.pdf` component for resume display
- Show success message with link to Jobs page
- Handle case where no PDF is generated (error state)

---

## 5. Implementation Phases

### Phase 1: Foundation
1. Add dependencies to `pyproject.toml`
2. Create Job database model
3. Update database initialization
4. Fix `data_adapter.py` to match current schema

### Phase 2: Resume Generation
1. Update agent input state with user information
2. Overhaul `create_resume` node for PDF generation
3. Update `ResumeService` for new workflow
4. Test PDF generation end-to-end

### Phase 3: User Interface
1. Create Jobs page with index view
2. Implement job detail dialog
3. Update Home page for PDF display
4. Add navigation for Jobs page

### Phase 4: Integration & Testing
1. End-to-end testing of resume generation
2. UI/UX testing of PDF display
3. Database integrity testing
4. Error handling validation

---

## 6. Error Handling Strategy

### 6.1 Basic Error Handling
- Use `logger.exception(e)` for full traceback logging
- Graceful degradation for missing user data
- Clear error messages in UI
- No complex file management or cleanup (YAGNI)

### 6.2 Error Scenarios
- Missing user information (name, email)
- PDF generation failures
- File system permission issues
- Database transaction failures

---

## 7. Future Extensibility

### 7.1 Template Selection
- Template selection will be handled at generation time
- No need to persist template choice in database
- Keep template selection logic separate from storage

### 7.2 Additional Job Data
- Schema designed to accommodate: company_name, job_title
- Future fields can be added without breaking changes
- Cover letters and other documents can be added later

### 7.3 File Management
- Current flat structure supports future organization
- UUID-based filenames prevent conflicts
- Simple structure allows for easy backup/restore

---

## 8. Technical Specifications

### 8.1 PDF Generation Pipeline
```
User Input → Agent Workflow → ResumeData → HTML Template → PDF File → Database Storage → UI Display
```

### 8.2 File Naming Convention
- Format: `{UUID4}.pdf`
- Example: `550e8400-e29b-41d4-a716-446655440000.pdf`
- Generated using Python's `uuid.uuid4()`

### 8.3 Template System
- Default template: `resume_001.html`
- Location: `src/features/resume/templates/`
- Rendered using Jinja2 templating engine
- HTML converted to PDF using WeasyPrint

---

## 9. Success Criteria

### 9.1 Functional Requirements
- [ ] Generate PDF resumes from job descriptions
- [ ] Save job applications with resume files
- [ ] Display PDF resumes in UI
- [ ] Navigate between job applications
- [ ] View job details with resume

### 9.2 Technical Requirements
- [ ] All dependencies properly installed
- [ ] Database schema updated and functional
- [ ] PDF generation working end-to-end
- [ ] UI components displaying PDFs correctly
- [ ] Error handling prevents crashes

### 9.3 User Experience
- [ ] Intuitive navigation to Jobs page
- [ ] Clear job application history
- [ ] Easy resume viewing in browser
- [ ] Responsive PDF display
- [ ] Clear error messages when issues occur
