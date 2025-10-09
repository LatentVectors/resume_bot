# Job Intake Flow with AI-Assisted Experience Enhancement and Resume Generation

## Sprint Overview

This sprint introduces a comprehensive, multi-step job intake flow that guides users through job creation, experience enhancement, and resume generation in a single cohesive workflow. The new flow leverages AI-powered gap analysis and conversational interfaces to help users create better-targeted resumes by enriching their work experience and iterating on resume drafts interactively.

### Key Goals
- Streamline the job-to-resume workflow with intelligent AI guidance
- Enhance user's work experience data through conversational AI assistance
- Enable iterative resume refinement with AI collaboration
- Persist complete workflow state for resumption and analysis
- Maintain backward compatibility with existing experience data

### Sprint Deliverables
1. Multi-step dialog flow for job intake (3 steps)
2. Enhanced Experience data model with Achievement support
3. AI-powered gap analysis comparing job requirements to user experience
4. Conversational experience enhancement with tool-based proposals
5. Interactive resume refinement with version management
6. Session persistence for interruption recovery
7. Profile page updates for new experience structure

---

## User Stories

### Story 1: Job Intake with AI Guidance
**As a** job seeker  
**I want to** paste a job description and be guided through a structured intake process  
**So that** I can create a targeted resume with minimal friction

**Acceptance Criteria:**
- User can paste job description on home page and click "Save"
- System extracts title/company and presents editable form
- User confirms/edits job details and saves to create job record
- Flow automatically proceeds to next step

### Story 2: Experience Gap Analysis
**As a** job seeker  
**I want to** see how my experience aligns with the job requirements  
**So that** I can understand my strengths and areas to emphasize

**Acceptance Criteria:**
- System analyzes job description against user's experience
- Report shows matched requirements, partial matches, and gaps
- Report is displayed as first message in chat interface
- Report helps guide the conversation about experience

### Story 3: Conversational Experience Enhancement
**As a** job seeker  
**I want to** have a conversation with AI that helps me articulate my experience better  
**So that** my resume reflects my full capabilities

**Acceptance Criteria:**
- AI asks targeted questions based on gap analysis
- AI proposes specific updates to experience records and achievements
- User can review, edit, and accept/reject each proposal
- Accepted changes immediately update the database
- User can proceed after engaging in at least one exchange

### Story 4: Interactive Resume Refinement
**As a** job seeker  
**I want to** collaborate with AI to refine my resume draft  
**So that** I can create a polished, targeted resume efficiently

**Acceptance Criteria:**
- Initial resume draft is generated using conversation context
- User sees chat interface alongside resume preview
- AI can update entire resume via tool calls
- User can make manual edits to resume content
- Both AI and manual changes create new versions
- User can switch between versions and see differences
- User pins desired version as final/canonical

### Story 5: Flow Interruption Recovery
**As a** job seeker  
**If I'm interrupted** during the intake flow  
**I want to** resume from where I left off  
**So that** I don't lose my progress

**Acceptance Criteria:**
- Job and session data persists after each step
- User can close browser and return later
- "Resume Intake Flow" button appears on job detail page
- Clicking button opens appropriate step based on session state
- Chat history and context are preserved

---

## Workflow & User Flow

### Step 1: Home Page - Job Entry
**User Action:**
1. User pastes job description into text area on home page
2. User clicks "Save" button

**System Action:**
- Triggers Background Task 1: Extract job details using LLM
- Opens Dialog View 1

---

### Background Task 1: Extract Job Details
**Implementation:** Existing `src/features/jobs/extraction.py`

**Function:** `extract_title_company(job_description: str) -> TitleCompany`
- Uses LLM call with structured output
- Extracts company name and job title from description
- Returns Pydantic model with extracted fields (may be None if extraction fails)

---

### Dialog View 1: Job Details Confirmation
**File:** `app/dialog/job_intake_flow.py` (function: `render_step1_details()`)

**UI Elements:**
- Progress indicator: "Step 1 of 3: Job Details" (plain text, top of dialog)
- Editable form fields:
  - Job Title (text input, required)
  - Company Name (text input, required)
  - Job Description (text area, required)
  - Favorite toggle (checkbox, optional)
- Single button: "Next"
  - Enabled only when title, company, and job description are all non-empty
  - No skip button - these fields are required

**User Actions:**
1. User reviews extracted title/company (pre-filled from Background Task 1)
2. User edits fields as needed
3. User clicks "Next"

**System Actions on Next:**
1. Save Job record to database with provided details
2. Create JobIntakeSession linked to job
3. Set `session_state.current_step = 2`
4. Call `st.rerun()` to re-render dialog showing View 2

---

### Background Task 2: Gap Analysis
**Implementation:** `src/features/jobs/gap_analysis.py`

**Function:** `analyze_job_experience_fit(job_description: str, experiences: list[Experience]) -> GapAnalysisReport`
- Uses single LLM call with structured output (Pydantic model)
- Analyzes job requirements against user's experience records
- Returns structured report containing:
  - `matched_requirements: list[str]` - Requirements the candidate clearly meets
  - `partial_matches: list[str]` - Requirements partially addressed
  - `gaps: list[str]` - Requirements not evidenced in experience
  - `suggested_questions: list[str]` - Targeted questions to ask the user

**GapAnalysisReport Model:**
```python
class GapAnalysisReport(BaseModel):
    matched_requirements: list[str]
    partial_matches: list[str]
    gaps: list[str]
    suggested_questions: list[str]
```

---

### Dialog View 2: Experience Gap Filling
**File:** `app/dialog/job_intake_flow.py` (function: `render_step2_experience()`)

**UI Elements:**
- Progress indicator: "Step 2 of 3: Experience Review" (plain text, top of dialog)
- Chat interface:
  - Gap analysis report as first AI message (plain text, non-editable)
  - Chat message area for user-AI conversation
  - AI-proposed updates shown as interactive cards
- Proposal cards (when AI makes proposals):
  - Editable form fields showing proposed changes
  - "Accept" button (saves to DB immediately)
  - "Reject" button (sends feedback to AI)
- Action buttons:
  - "Skip" (always enabled, proceeds to next step with summarization)
  - "Next" (enabled after user provides at least one response)

**Workflow:**
1. Gap analysis report displayed as first AI message
2. User engages in conversation with AI
3. AI uses tool calling to propose specific updates:
   - `propose_experience_update(experience_id, company_overview?, role_overview?, skills?)` - Update existing experience
   - `propose_achievement_update(achievement_id, content)` - Update existing achievement
   - `propose_new_achievement(experience_id, content, order?)` - Add new achievement to experience
4. For each proposal:
   - UI displays editable card with proposed changes
   - User can edit before accepting
   - On Accept: immediately save via ExperienceService, update chat context
   - On Reject: send feedback to AI in next message
5. User clicks "Next" or "Skip" to proceed

**System Actions on Next/Skip:**
1. Trigger Background Task 3 (conversation summarization)
2. Set `session_state.current_step = 3`
3. Call `st.rerun()` to re-render dialog showing View 3

**Chat Agent Architecture:**
- Simple LangChain chat model with tool binding (not a full agent)
- Tools defined as Pydantic models/functions
- Dialog maintains chat history in session state
- Message flow: user message → append to history → call LLM with tools → handle tool calls → update UI

**Important Notes:**
- No undo functionality to avoid edge cases
- Proposals are NOT automatically applied - user must explicitly accept
- Both Skip and Next trigger conversation summarization

---

### Background Task 3: Context Summarization and Initial Resume
**Implementation:** `src/features/jobs/intake_context.py`

**Function 1: `summarize_intake_conversation(messages: list[dict], gap_analysis: GapAnalysisReport) -> str`**
- Takes full chat history from View 2 and gap analysis report
- Uses LLM (GPT-4 or similar) with structured prompt
- Extracts key insights focusing on:
  - Additional context provided by user beyond written experience
  - Unique details, motivations, and interests expressed
  - User's fit assessment based on gap analysis and responses
  - Clarifications or nuances refining understanding of background
- Returns concise summary (2-4 paragraphs) as string
- Summary stored in `JobIntakeSession.conversation_summary`

**Function 2: `generate_resume_from_conversation(job_id: int, user_id: int, conversation_summary: str, chat_history: list[dict]) -> ResumeData`**
- New LLM function specifically for generating resume from intake conversation
- **Does NOT use Response records** (out of scope for this sprint)
- Takes conversation summary and full chat history as primary inputs
- Fetches user profile data and experiences (including new achievements) from database
- Uses existing resume generation agent with conversation context enriching generation
- Returns ResumeData used to create first version in View 3

---

### Dialog View 3: Resume Refinement
**File:** `app/dialog/job_intake_flow.py` (function: `render_step3_resume()`)

**UI Elements:**
- Progress indicator: "Step 3 of 3: Resume Review" (plain text, top of dialog)
- Two-column layout [1:1]:
  - **Left column:** Chat interface with history
  - **Right column:** Resume content area
    - Version selector dropdown at top (matches job detail tabs)
    - Toggle: PDF preview ↔ editable content form
    - Copy and download buttons below PDF preview
- Action buttons:
  - "Skip" (always enabled, completes flow without pinning)
  - "Next" (enabled after user selects a version from dropdown)

**Chat Agent Architecture:**
- Simple LangChain chat model with single tool: `update_resume_draft`
- Tool signature accepts full ResumeData Pydantic model:
  ```python
  update_resume_draft(
      title: str,
      professional_summary: str,
      skills: list[str],
      experience: list[ExperienceData],
      education: list[EducationData],
      certifications: list[CertificationData],
      ...
  )
  ```
- AI can make changes to entire resume on behalf of user
- Each tool call automatically:
  - Saves new ResumeVersion to database
  - Updates the preview display
  - Returns confirmation to chat

**Version Management:**
- User can make manual edits in form view → saves new ResumeVersion
- User can switch versions via dropdown → updates AI system instructions
- Version pinning identical to resume tab in job detail page:
  - User selects version from dropdown
  - "Next" calls `ResumeService.pin_canonical(job_id, version_id)`
  - Updates canonical Resume row
  - "Skip" completes without pinning (no canonical resume)

**User Actions:**
1. User iterates on resume through chat and/or manual edits
2. User selects desired version from dropdown (if pinning)
3. User clicks "Next" to pin and complete OR "Skip" to complete without pinning

**System Actions on Next:**
1. Call `ResumeService.pin_canonical(job_id, selected_version_id)`
2. Mark JobIntakeSession as completed (`completed_at = now()`)
3. Navigate to job detail overview tab

**System Actions on Skip:**
1. Mark JobIntakeSession as completed (no canonical resume set)
2. Navigate to job detail overview tab

---

### Job Detail - Overview Tab Enhancement
**File:** `app/pages/job_tabs/overview.py`

**New UI Element:**
- "Resume job intake workflow" button
  - Material icon: `edit_note`
  - Help text: "Resume job intake workflow"
  - Hidden if job status is "Applied" (locked state)
  - Same icon/text regardless of resume vs restart

**Button Behavior:**
1. Check if JobIntakeSession exists for job
2. If exists and incomplete: set `session_state.current_step = session.current_step`
3. If complete or doesn't exist: set `session_state.current_step = 1`
4. Open intake flow dialog (`show_job_intake_dialog()`)
5. Dialog renders appropriate step based on `current_step`

**Post-Flow:**
- All resume versions from intake visible in resume tab
- User can continue refining using existing job detail UI

---

## Data Models

### Enhanced Experience Model
**File:** `src/database.py`

**Existing fields (unchanged):**
```python
class Experience(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    company_name: str
    job_title: str
    location: str | None = Field(default=None)
    start_date: date
    end_date: date | None = Field(default=None)
    content: str  # Keep for backward compatibility
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

**New fields to add:**
```python
    company_overview: str | None = Field(default=None)  # Brief summary of the company
    role_overview: str | None = Field(default=None)  # Brief summary of the role
    skills: list[str] = Field(default_factory=list)  # Array of skill strings (stored as JSON)
```

**Migration:**
- Add nullable columns to existing table
- No automatic data migration from `content` to new fields
- Existing records continue to work with `content` field
- Users gradually enhance via intake flow or manual editing

---

### New Achievement Model
**File:** `src/database.py`

```python
class Achievement(SQLModel, table=True):
    """Achievement entries linked to specific work experiences.
    
    One-to-many relationship: each experience can have multiple achievements.
    """
    id: int | None = Field(default=None, primary_key=True)
    experience_id: int = Field(foreign_key="experience.id")
    content: str  # Detailed achievement description
    order: int = Field(default=0)  # For ordering achievements within experience
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

**Relationship:**
- Foreign key to Experience
- Multiple achievements per experience
- `order` field for user-controlled ordering

---

### JobIntakeSession Model
**File:** `src/database.py`

```python
class JobIntakeSession(SQLModel, table=True):
    """Tracks state of job intake workflow for resumption and analytics.
    
    Unique constraint on job_id ensures one active session per job.
    """
    id: int | None = Field(default=None, primary_key=True)
    job_id: int = Field(foreign_key="job.id", unique=True)
    current_step: int  # 1, 2, or 3
    step1_completed: bool = Field(default=False)
    step2_completed: bool = Field(default=False)
    step3_completed: bool = Field(default=False)
    gap_analysis_json: str | None = Field(default=None)  # Stores GapAnalysisReport
    conversation_summary: str | None = Field(default=None)  # Summary from step 2
    completed_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

**Usage:**
- Created when job saved in View 1
- Updated after each step completion
- `completed_at` set when View 3 completes
- Enables resumption from interruption

---

### JobIntakeChatMessage Model
**File:** `src/database.py`

```python
class JobIntakeChatMessage(SQLModel, table=True):
    """Stores chat history for intake flow steps 2 and 3.
    
    Messages stored as JSON to accommodate any LangChain message format.
    """
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="jobintakesession.id")
    step: int  # 2 or 3
    messages: str  # JSON array of LangChain message format
    created_at: datetime = Field(default_factory=datetime.now)
```

**Usage:**
- Each step appends messages to history
- Stored as JSON for flexibility with LangChain formats
- Enables conversation resumption and review

---

## Service Layer

### ExperienceService (New)
**File:** `app/services/experience_service.py`

**Methods:**
```python
class ExperienceService:
    @staticmethod
    def update_experience_fields(
        experience_id: int,
        company_overview: str | None = None,
        role_overview: str | None = None,
        skills: list[str] | None = None
    ) -> Experience:
        """Update enhanced fields on an experience."""
        
    @staticmethod
    def add_achievement(
        experience_id: int,
        content: str,
        order: int | None = None
    ) -> Achievement:
        """Add a new achievement to an experience."""
        
    @staticmethod
    def update_achievement(achievement_id: int, content: str) -> Achievement:
        """Update an existing achievement's content."""
        
    @staticmethod
    def delete_achievement(achievement_id: int) -> bool:
        """Delete an achievement."""
        
    @staticmethod
    def reorder_achievements(
        experience_id: int,
        achievement_ids_in_order: list[int]
    ) -> list[Achievement]:
        """Reorder achievements for an experience."""
        
    @staticmethod
    def get_experience_with_achievements(experience_id: int) -> tuple[Experience, list[Achievement]]:
        """Get experience with all its achievements."""
```

---

### JobService Extensions
**File:** `app/services/job_service.py`

**New methods to add:**
```python
class JobService:
    # Existing methods unchanged...
    
    @staticmethod
    def create_intake_session(job_id: int) -> JobIntakeSession:
        """Create a new intake session for a job."""
        
    @staticmethod
    def get_intake_session(job_id: int) -> JobIntakeSession | None:
        """Get the intake session for a job."""
        
    @staticmethod
    def update_session_step(
        session_id: int,
        step: int,
        completed: bool = False
    ) -> JobIntakeSession:
        """Update the current step and optionally mark it completed."""
        
    @staticmethod
    def save_gap_analysis(session_id: int, gap_analysis_json: str) -> JobIntakeSession:
        """Save gap analysis report to session."""
        
    @staticmethod
    def save_conversation_summary(session_id: int, summary: str) -> JobIntakeSession:
        """Save conversation summary to session."""
        
    @staticmethod
    def complete_session(session_id: int) -> JobIntakeSession:
        """Mark session as completed."""
```

---

### ChatMessageService (New)
**File:** `app/services/chat_message_service.py`

```python
class ChatMessageService:
    @staticmethod
    def append_messages(
        session_id: int,
        step: int,
        messages_json: str
    ) -> JobIntakeChatMessage:
        """Append messages to chat history for a step."""
        
    @staticmethod
    def get_messages_for_step(session_id: int, step: int) -> list[dict]:
        """Get all messages for a specific step."""
        
    @staticmethod
    def get_full_conversation(session_id: int) -> dict[int, list[dict]]:
        """Get complete conversation history grouped by step."""
```

---

## Feature Modules

### Gap Analysis
**File:** `src/features/jobs/gap_analysis.py`

**Pydantic Model:**
```python
class GapAnalysisReport(BaseModel):
    """Structured report comparing job requirements to candidate experience."""
    matched_requirements: list[str]
    partial_matches: list[str]
    gaps: list[str]
    suggested_questions: list[str]
```

**Function:**
```python
def analyze_job_experience_fit(
    job_description: str,
    experiences: list[Experience]
) -> GapAnalysisReport:
    """
    Analyze how candidate's experience aligns with job requirements.
    
    Uses LLM with structured output to identify:
    - Requirements clearly met by candidate's experience
    - Requirements partially addressed (need emphasis/reframing)
    - Requirements not evidenced (potential gaps)
    - Suggested questions to ask candidate
    
    Args:
        job_description: Full text of job description
        experiences: List of candidate's experience records
        
    Returns:
        Structured gap analysis report
    """
```

**Implementation Notes:**
- Use single LLM call with structured output (Pydantic model)
- Prompt should analyze requirements systematically
- Return empty lists for sections if no matches/gaps found
- Handle LLM failures gracefully (return empty report with error flag)

---

### Intake Context Functions
**File:** `src/features/jobs/intake_context.py`

**Function 1: Conversation Summarization**
```python
def summarize_intake_conversation(
    messages: list[dict],
    gap_analysis: GapAnalysisReport
) -> str:
    """
    Summarize key insights from intake conversation.
    
    Extracts and synthesizes:
    - Additional context beyond written experience
    - Unique details, motivations, interests expressed
    - Fit assessment based on gap analysis and responses
    - Clarifications refining understanding of background
    
    Args:
        messages: Full chat history from View 2 (LangChain format)
        gap_analysis: The gap analysis report from View 2
        
    Returns:
        Concise summary (2-4 paragraphs) as string
    """
```

**Function 2: Resume Generation from Conversation**
```python
def generate_resume_from_conversation(
    job_id: int,
    user_id: int,
    conversation_summary: str,
    chat_history: list[dict]
) -> ResumeData:
    """
    Generate initial resume draft using intake conversation context.
    
    This function is specifically for intake flow and does NOT use
    Response records (those are out of scope for this sprint).
    
    Args:
        job_id: ID of the job being applied to
        user_id: ID of the user
        conversation_summary: Summary from summarize_intake_conversation()
        chat_history: Full chat history from View 2
        
    Returns:
        ResumeData ready for creating first version in View 3
        
    Implementation:
        - Fetch user profile data and experiences (including achievements) from DB
        - Use existing resume generation agent
        - Enrich agent with conversation context via summary and chat history
        - Return generated ResumeData
    """
```

---

## UI Implementation

### Dialog Architecture
**File:** `app/dialog/job_intake_flow.py`

**Main Dialog Function:**
```python
@st.dialog("Job Intake", width="large")
def show_job_intake_dialog(
    initial_title: str | None = None,
    initial_company: str | None = None,
    initial_description: str = "",
    job_id: int | None = None
) -> None:
    """
    Main intake flow dialog with step-based rendering.
    
    Uses session_state.current_step to determine which step to render.
    Each step is isolated in its own render function.
    
    Args:
        initial_title: Pre-filled job title from extraction
        initial_company: Pre-filled company from extraction
        initial_description: Job description text
        job_id: Existing job ID (for resumption)
    """
    # Initialize session state if needed
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
        
    # Render appropriate step
    if st.session_state.current_step == 1:
        render_step1_details(initial_title, initial_company, initial_description)
    elif st.session_state.current_step == 2:
        render_step2_experience(job_id)
    elif st.session_state.current_step == 3:
        render_step3_resume(job_id)
```

**Step Render Functions:**
```python
def render_step1_details(
    initial_title: str | None,
    initial_company: str | None,
    initial_description: str
) -> None:
    """Render Step 1: Job details confirmation."""
    # Display progress: "Step 1 of 3: Job Details"
    # Render form with title, company, description, favorite
    # Single "Next" button (enabled when all required fields filled)
    # On Next: save job, create session, set current_step=2, st.rerun()
    
def render_step2_experience(job_id: int) -> None:
    """Render Step 2: Experience gap filling chat."""
    # Display progress: "Step 2 of 3: Experience Review"
    # Show gap analysis as first AI message
    # Render chat interface
    # Handle tool calls for experience proposals
    # "Skip" and "Next" buttons
    # On Skip/Next: summarize conversation, set current_step=3, st.rerun()
    
def render_step3_resume(job_id: int) -> None:
    """Render Step 3: Resume refinement chat."""
    # Display progress: "Step 3 of 3: Resume Review"
    # Two-column layout: chat | resume preview
    # Handle resume update tool calls
    # Version selector and toggle
    # "Skip" and "Next" buttons
    # On Next: pin version, complete session, navigate to job detail
    # On Skip: complete session without pinning, navigate to job detail
```

**Progress Indicator Pattern:**
```python
# At top of each render function:
st.caption("Step 1 of 3: Job Details")  # Or Step 2, Step 3
st.markdown("---")
```

**Transition Pattern:**
```python
# When transitioning to next step:
st.session_state.current_step = 2  # or 3
st.rerun()
```

---

### Profile Page Updates
**File:** `app/pages/profile.py` and `app/dialog/experience_dialog.py`

**Experience Form Enhancements:**
1. Add "Company Overview" field (text area, optional)
2. Add "Role Overview" field (text area, optional)
3. Add "Skills" field (multi-select tag input for array of strings)
4. Keep all existing fields unchanged

**Achievement Management UI:**
1. Within each experience, add "Achievements" section
2. Display ordered list of achievements with:
   - Content display
   - Edit button (opens achievement dialog)
   - Delete button (with confirmation)
   - Drag handles for reordering
3. "Add Achievement" button
4. Save reorder changes to `order` field

**Dialog Updates:**
- Update `show_add_experience_dialog()` to include new fields
- Update `show_edit_experience_dialog()` to include new fields
- Create `show_add_achievement_dialog(experience_id)`
- Create `show_edit_achievement_dialog(achievement_id)`
- Create `show_delete_achievement_dialog(achievement_id)`

---

### Home Page Integration
**File:** `app/pages/home.py`

**Update "Save" Button Handler:**
```python
# OLD: Opens simple job_save_dialog
# NEW: Opens intake flow dialog

if save_clicked:
    try:
        # Extract title/company (existing logic)
        from src.features.jobs.extraction import extract_title_company
        extracted = extract_title_company(user_input or "")
        
        initial_title = getattr(extracted, "title", None) if extracted else None
        initial_company = getattr(extracted, "company", None) if extracted else None
        
        # Open intake flow dialog instead of simple save dialog
        from app.dialog.job_intake_flow import show_job_intake_dialog
        show_job_intake_dialog(
            initial_title=initial_title,
            initial_company=initial_company,
            initial_description=user_input or ""
        )
    except Exception as e:
        st.error("Unable to open intake dialog.")
        logger.error(f"Error launching intake: {e}")
```

---

### Job Detail Overview Tab
**File:** `app/pages/job_tabs/overview.py`

**Add Resume Flow Button:**
```python
# Check if job is applied (hide button if locked)
if job.status != "Applied":
    # Get intake session to determine button state
    session = JobService.get_intake_session(job.id)
    
    # Determine if resuming or restarting
    if session and session.completed_at is None:
        # Incomplete session - can resume
        tooltip = "Resume job intake workflow"
        current_step = session.current_step
    else:
        # No session or completed - can restart
        tooltip = "Resume job intake workflow"
        current_step = 1
    
    # Button with edit_note icon
    if st.button(
        "📝 Resume Intake",  # Using emoji, or use Streamlit's icon feature
        help=tooltip,
        key="resume_intake_flow"
    ):
        st.session_state.current_step = current_step
        from app.dialog.job_intake_flow import show_job_intake_dialog
        show_job_intake_dialog(job_id=job.id)
```

---

## Error Handling & Recovery

### Job Persistence
- Job record saved after clicking "Next" in View 1
- JobIntakeSession created and linked at same time
- Session tracks current step and completion status

### Flow Interruption Recovery
**If flow crashes or is interrupted:**
1. User redirected to job detail page (overview tab)
2. JobIntakeSession preserves state (`current_step`, completed flags)
3. "Resume Intake Flow" button shows on overview tab
4. Clicking button:
   - Reads session state to determine current step
   - Opens dialog at appropriate step
   - Chat history and context restored from database

### LLM Call Failures
**Graceful degradation for each task:**

1. **Extraction in View 1:**
   - Display error message
   - Allow user to proceed with manual entry (fields empty)
   - Don't block progression

2. **Gap Analysis in View 2:**
   - Display error message
   - Allow proceeding without report
   - Chat still functional for experience discussion

3. **Resume Generation in View 3:**
   - Display error message
   - Allow manual resume creation or retry
   - User can skip to complete flow

### Workflow State Persistence
**Complete state persisted for:**
- Resuming from current step after interruption
- Reviewing gap analysis and conversation history
- Tracking versions created during intake
- Future analytics and flow improvement

---

## Migration & Backward Compatibility

### Database Migration Steps
1. Add columns to `Experience` table:
   ```sql
   ALTER TABLE experience ADD COLUMN company_overview TEXT NULL;
   ALTER TABLE experience ADD COLUMN role_overview TEXT NULL;
   ALTER TABLE experience ADD COLUMN skills JSON NULL;
   ```

2. Create `Achievement` table:
   ```sql
   CREATE TABLE achievement (
       id INTEGER PRIMARY KEY,
       experience_id INTEGER NOT NULL,
       content TEXT NOT NULL,
       order INTEGER DEFAULT 0,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (experience_id) REFERENCES experience(id)
   );
   ```

3. Create `JobIntakeSession` table:
   ```sql
   CREATE TABLE jobintakesession (
       id INTEGER PRIMARY KEY,
       job_id INTEGER NOT NULL UNIQUE,
       current_step INTEGER NOT NULL,
       step1_completed BOOLEAN DEFAULT 0,
       step2_completed BOOLEAN DEFAULT 0,
       step3_completed BOOLEAN DEFAULT 0,
       gap_analysis_json TEXT NULL,
       conversation_summary TEXT NULL,
       completed_at TIMESTAMP NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (job_id) REFERENCES job(id)
   );
   ```

4. Create `JobIntakeChatMessage` table:
   ```sql
   CREATE TABLE jobintakechatmessage (
       id INTEGER PRIMARY KEY,
       session_id INTEGER NOT NULL,
       step INTEGER NOT NULL,
       messages TEXT NOT NULL,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       FOREIGN KEY (session_id) REFERENCES jobintakesession(id)
   );
   ```

### Data Migration Strategy
- **No automatic migration** from `content` → new fields
- Existing experiences retain `content` field (no data loss)
- New fields are nullable/optional
- Users enhance experiences over time via:
  - Intake flow conversations
  - Manual profile editing

### Backward Compatibility
- Old experience format still displayed/editable in profile
- Resume generation agent handles varying data completeness
- View 2 tools work with experiences having only legacy fields
- Gradual migration as users engage with system

---

## Implementation Sequence

### Phase 1: Data Models
**Tasks:**
1. Update `Experience` model in `src/database.py`
   - Add `company_overview`, `role_overview`, `skills` fields
   - Ensure SQLModel handles JSON field for skills array

2. Create `Achievement` model in `src/database.py`
   - One-to-many relationship with Experience
   - Include `order` field for sorting

3. Create `JobIntakeSession` model in `src/database.py`
   - Unique constraint on `job_id`
   - Track step progress and completion

4. Create `JobIntakeChatMessage` model in `src/database.py`
   - Link to session, store messages as JSON

5. Run database migration (add tables/columns)

6. Create/update service layer:
   - `app/services/experience_service.py` (new)
   - `app/services/job_service.py` (extend)
   - `app/services/chat_message_service.py` (new)

**Validation:**
- Test CRUD operations for all new models
- Verify backward compatibility with existing experiences
- Confirm foreign key relationships work correctly

---

### Phase 2: Profile UI Updates
**Tasks:**
1. Update `app/dialog/experience_dialog.py`:
   - Add company_overview field to forms
   - Add role_overview field to forms
   - Add skills multi-select/tag input

2. Create achievement dialogs:
   - `show_add_achievement_dialog(experience_id)`
   - `show_edit_achievement_dialog(achievement_id)`
   - `show_delete_achievement_dialog(achievement_id)` with confirmation

3. Update `app/pages/profile.py`:
   - Add "Achievements" section to each experience
   - Display ordered list with edit/delete/reorder
   - "Add Achievement" button

4. Implement reordering:
   - Drag-and-drop or up/down buttons
   - Save new order via `ExperienceService.reorder_achievements()`

**Validation:**
- Test all CRUD operations for achievements
- Verify reordering persists correctly
- Check UI displays new and legacy experiences properly

---

### Phase 3: Gap Analysis
**Tasks:**
1. Create `src/features/jobs/gap_analysis.py`
2. Define `GapAnalysisReport` Pydantic model
3. Implement `analyze_job_experience_fit()` function:
   - Use LLM with structured output
   - Handle various job description formats
   - Gracefully handle LLM failures

4. Create comprehensive prompt for gap analysis:
   - Extract requirements from job description
   - Match against experience content
   - Identify matches, partial matches, gaps
   - Generate targeted questions

**Validation:**
- Test with various job descriptions (technical, non-technical)
- Test with users having different experience levels
- Verify report structure matches Pydantic model
- Test error handling when LLM fails

---

### Phase 4: Dialog Views (Sequential)
**Tasks:**
1. Create `app/dialog/job_intake_flow.py` with main structure:
   - `show_job_intake_dialog()` main function
   - Session state initialization
   - Step routing logic

2. Implement Step 1: `render_step1_details()`:
   - Progress indicator
   - Form with validation
   - "Next" button with enablement logic
   - Save job and create session on Next
   - Transition to Step 2

3. Implement Step 2: `render_step2_experience()`:
   - Progress indicator
   - Display gap analysis report
   - Chat interface implementation
   - LangChain tool setup for proposals
   - Proposal card UI (editable, accept/reject)
   - "Skip" and "Next" buttons
   - Transition to Step 3

4. Implement Step 3: `render_step3_resume()`:
   - Progress indicator
   - Two-column layout (chat | resume)
   - Version selector and toggle
   - LangChain tool for resume updates
   - Manual edit handling
   - "Skip" and "Next" buttons
   - Session completion and navigation

**Validation:**
- Test each step independently
- Test transitions between steps (session state management)
- Verify button enablement rules
- Test chat functionality in Steps 2 and 3
- Verify proposal and resume update flows

---

### Phase 5: Context & Resume Generation
**Tasks:**
1. Create `src/features/jobs/intake_context.py`

2. Implement `summarize_intake_conversation()`:
   - Create comprehensive prompt for summarization
   - Extract key insights from chat history
   - Return concise 2-4 paragraph summary

3. Implement `generate_resume_from_conversation()`:
   - Fetch user data and experiences with achievements
   - Build enriched context with conversation summary
   - Call resume generation agent
   - Return ResumeData

4. Integrate with dialog:
   - Call summarization when leaving Step 2
   - Call resume generation before entering Step 3
   - Handle generation failures gracefully

**Validation:**
- Test summarization with various conversation lengths
- Verify summary captures key points
- Test resume generation with conversation context
- Compare resumes with/without conversation context
- Verify no Response records created (out of scope)

---

### Phase 6: Integration
**Tasks:**
1. Update `app/pages/home.py`:
   - Change "Save" button handler
   - Open intake flow dialog instead of simple save dialog
   - Pass extracted title/company to dialog

2. Update `app/pages/job_tabs/overview.py`:
   - Add "Resume job intake workflow" button
   - Use `edit_note` icon with help text
   - Hide when job status is "Applied"
   - Handle resume vs restart logic
   - Open dialog at appropriate step

3. End-to-end testing:
   - Complete flow from home page through all steps
   - Test Skip buttons at each step
   - Test interruption and resumption
   - Test with various job descriptions
   - Verify version history in job detail

**Validation:**
- Full workflow testing (happy path)
- Test all Skip/Next combinations
- Test interruption at each step and resume
- Verify data persistence throughout
- Check job detail integration
- Confirm backward compatibility maintained

---

## Testing Checklist

### Data Model Testing
- [ ] Create experience with new fields (company_overview, role_overview, skills)
- [ ] Create achievement linked to experience
- [ ] Update achievement content
- [ ] Delete achievement
- [ ] Reorder achievements for an experience
- [ ] Verify backward compatibility with legacy experiences (no new fields)
- [ ] Test skills array storage and retrieval (JSON handling)

### Service Layer Testing
- [ ] `ExperienceService.update_experience_fields()` with various field combinations
- [ ] `ExperienceService.add_achievement()` with and without order
- [ ] `ExperienceService.update_achievement()` content updates
- [ ] `ExperienceService.delete_achievement()` removes record
- [ ] `ExperienceService.reorder_achievements()` updates order correctly
- [ ] `JobService.create_intake_session()` creates unique session per job
- [ ] `JobService.update_session_step()` tracks progress
- [ ] `ChatMessageService.append_messages()` stores JSON correctly

### Gap Analysis Testing
- [ ] Test with technical job description
- [ ] Test with non-technical job description
- [ ] Test with entry-level vs senior-level jobs
- [ ] Test with candidate having strong match
- [ ] Test with candidate having weak match
- [ ] Verify report structure (matched, partial, gaps, questions)
- [ ] Test LLM failure handling

### Dialog Flow Testing
- [ ] **Step 1 - Button Enablement:**
  - [ ] "Next" disabled when fields empty
  - [ ] "Next" enabled when all required fields filled
  - [ ] No "Skip" button present

- [ ] **Step 2 - Button Enablement:**
  - [ ] "Next" disabled initially
  - [ ] "Next" enabled after user sends at least one message
  - [ ] "Skip" always enabled

- [ ] **Step 3 - Button Enablement:**
  - [ ] "Next" disabled when no version selected
  - [ ] "Next" enabled when version selected
  - [ ] "Skip" always enabled

- [ ] **Dialog Transitions:**
  - [ ] Step 1 → Step 2 (save job, create session)
  - [ ] Step 2 → Step 3 (run summarization)
  - [ ] Step 3 → Job detail (complete session)

- [ ] **Skip Button Behavior:**
  - [ ] Step 2 Skip: runs summarization before proceeding
  - [ ] Step 3 Skip: completes flow without pinning (no canonical resume)

### Chat & Tool Calling Testing
- [ ] View 2: AI proposes experience update
- [ ] View 2: User edits proposal before accepting
- [ ] View 2: User accepts proposal → saves to DB
- [ ] View 2: User rejects proposal → feedback to AI
- [ ] View 3: AI proposes resume update
- [ ] View 3: Resume update creates new version
- [ ] View 3: Manual edit creates new version
- [ ] View 3: Version selector updates AI context

### Session Persistence & Recovery Testing
- [ ] Interrupt at Step 1 → resume shows Step 1
- [ ] Interrupt at Step 2 → resume shows Step 2 with chat history
- [ ] Interrupt at Step 3 → resume shows Step 3 with versions
- [ ] "Resume Intake Flow" button shows correct state
- [ ] Button hidden when job is "Applied"
- [ ] Correct icon (`edit_note`) and text displayed

### Version Management Testing
- [ ] Switching versions updates preview
- [ ] "Next" pins selected version as canonical
- [ ] "Skip" completes without pinning
- [ ] Versions from intake visible in job detail resume tab
- [ ] Can continue refining from job detail after intake

### Conversation & Resume Generation Testing
- [ ] Summarization captures key conversation points
- [ ] Summary stored in session
- [ ] Resume generation includes conversation context
- [ ] Resume without conversation context (for comparison)
- [ ] Resume reflects accepted experience updates
- [ ] Resume reflects new achievements

### Integration Testing
- [ ] Home page "Save" triggers intake flow
- [ ] Job created and session initialized
- [ ] Complete flow creates job, updates experiences, generates resume
- [ ] Job detail "Resume Intake" button works
- [ ] All versions accessible from job detail

### Backward Compatibility Testing
- [ ] Legacy experiences (no new fields) display correctly
- [ ] Legacy experiences editable in profile
- [ ] View 2 tools work with legacy experiences
- [ ] Resume generation handles missing new fields
- [ ] No data loss for existing records

### Critical Validations
- [ ] **Response records NOT created in intake flow** (out of scope)
- [ ] No undo functionality (by design)
- [ ] Session state persists across reruns
- [ ] LLM failures don't break flow (graceful degradation)
- [ ] All step transitions update database correctly

---

## Key Dependencies

### Required Libraries
- **LangChain**: Chat models and tool calling
- **Streamlit**: Dialog UI and session state
- **Pydantic**: Structured outputs and data validation
- **SQLModel**: Database models and relationships

### Existing Infrastructure (Reuse)
- Resume generation agent (`src/agents/main/`)
- `ResumeService` for version management
- `JobService` for job operations
- PDF rendering services
- LLM integration via `src/core/models.py`

---

## Design Decisions & Rationale

### Why Single Dialog with Step Functions?
- **Simpler state management**: One dialog lifecycle, easier session state
- **Better code organization**: Each step isolated in own function
- **Easier transitions**: Just update `current_step` and `st.rerun()`
- **Less complexity**: Avoid multiple dialog open/close cycles

### Why No Undo Functionality?
- **Edge case avoidance**: Complex state management with chat history
- **Database consistency**: Simpler to maintain data integrity
- **User control**: Users can reject proposals before accepting

### Why Plain Text Progress Indicator?
- **Simplicity**: Avoid custom CSS/HTML complexity
- **Consistency**: Works reliably across Streamlit versions
- **Focus**: Users focus on content, not visual indicators

### Why Store Chat as JSON?
- **Flexibility**: Accommodate any LangChain message format
- **Future-proof**: Format changes won't break storage
- **Simplicity**: No complex ORM relationships for messages

### Why Separate Achievement Model?
- **Granularity**: Easier to target specific achievements in proposals
- **Reusability**: Achievements can be referenced independently
- **Ordering**: Explicit control over achievement display order

### Why Skip Still Runs Summarization?
- **Context preservation**: Summary valuable even without proposals
- **Resume quality**: Conversation insights improve generation
- **Consistency**: Always capture conversation value

---

## Success Criteria

### Sprint is complete when:
1. ✅ All data models created and migrated
2. ✅ Profile page supports new experience structure
3. ✅ Three-step intake dialog fully functional
4. ✅ Gap analysis generates structured reports
5. ✅ Experience proposals editable and persistable
6. ✅ Resume generation includes conversation context
7. ✅ Version management and pinning works
8. ✅ Session persistence enables resumption
9. ✅ Home page and job detail integrated
10. ✅ All tests passing
11. ✅ Backward compatibility maintained
12. ✅ Documentation complete

### Quality Gates
- No Response records created (verified)
- LLM failures handled gracefully
- Session state never corrupts
- All transitions save to database
- Button enablement rules enforced
- Legacy data continues to work

