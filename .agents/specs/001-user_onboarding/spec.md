# User Onboarding Specification

## Overview
Transform the multi-user app into a single-user application with a guided onboarding experience for first-time users. When no user exists in the database, new users will be guided through a step-by-step setup process.

## User Experience Flow

### 1. First-Time User Detection
- **Trigger**: App startup checks if any users exist in database
- **Behavior**: If no users found, redirect to onboarding flow instead of normal navigation
- **State**: Normal navigation disabled until onboarding completion

### 2. Onboarding Steps
1. **Basic User Information** (Required - User Created After This Step)
   - First Name (required)
   - Last Name (required)
   - Phone Number (optional)
   - Email (optional)
   - Address (optional)
   - City (optional)
   - State (optional)
   - ZIP Code (optional)
   - LinkedIn Profile URL (optional)
   - GitHub Profile URL (optional)
   - Website URL (optional)

2. **Work Experience Setup** (Optional - Can Skip)
   - Add work experience entries (optional)
   - Company Name (required if adding)
   - Job Title (required if adding)
   - Start Date (required if adding - ISO date format)
   - End Date (optional if adding - ISO date format, for current positions)
   - Description/Content (required if adding)

3. **Education Setup** (Optional - Can Skip)
   - Add education entries (optional)
   - School/Institution (required if adding)
   - Degree (required if adding)
   - Start Date (required if adding - ISO date format)
   - End Date (required if adding - ISO date format)

**Note**: User is created after Step 1. Steps 2 and 3 are optional and can be skipped. User can add experience/education later from the user page.

## Technical Implementation

### Database Models

#### Enhanced User Model
```python
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    phone_number: str | None = Field(default=None)
    email: str | None = Field(default=None)
    address: str | None = Field(default=None)
    city: str | None = Field(default=None)
    state: str | None = Field(default=None)
    zip_code: str | None = Field(default=None)
    linkedin_url: str | None = Field(default=None)
    github_url: str | None = Field(default=None)
    website_url: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

#### New Experience Model
```python
class Experience(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    company_name: str
    job_title: str
    start_date: date  # ISO date format (YYYY-MM-DD)
    end_date: date | None = Field(default=None)  # ISO date format (YYYY-MM-DD)
    content: str
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

#### New Education Model
```python
class Education(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    school: str
    degree: str
    start_date: date  # ISO date format (YYYY-MM-DD)
    end_date: date    # ISO date format (YYYY-MM-DD)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

### Page Structure

#### Onboarding Implementation
- `pages/_onboarding.py` - Single onboarding page with step navigation (hidden from nav)
- Steps 1-3 implemented within the single onboarding page
- After Step 1 completion, user is created and redirected to home page

#### Updated Main Navigation
- Modify `app/main.py` to check for user existence
- Redirect to onboarding if no users exist
- If user exists, redirect directly to home page (skip users list page)
- After onboarding completion, redirect to home page
- Hide onboarding page from normal navigation using underscore prefix
- Replace `pages/users.py` with `pages/user.py` for single user profile view

### Service Layer Updates

#### UserService Enhancements
```python
class UserService:
    @staticmethod
    def has_users() -> bool:
        """Check if any users exist in the database."""
        
    @staticmethod
    def get_current_user() -> User | None:
        """Get the single user (for single-user app)."""
        
    @staticmethod
    def create_user(**user_data) -> int:
        """Create a new user with all metadata fields."""
        
    @staticmethod
    def update_user(user_id: int, **updates) -> User | None:
        """Update user information and set updated_at timestamp."""
```

#### New ExperienceService
```python
class ExperienceService:
    @staticmethod
    def create_experience(user_id: int, **data) -> int:
        """Create a new experience entry with created_at/updated_at timestamps."""
        
    @staticmethod
    def list_user_experiences(user_id: int) -> list[Experience]:
        """Get all experiences for a user."""
        
    @staticmethod
    def update_experience(experience_id: int, **updates) -> Experience | None:
        """Update an experience entry and set updated_at timestamp."""
        
    @staticmethod
    def delete_experience(experience_id: int) -> bool:
        """Delete an experience entry."""
```

#### New EducationService
```python
class EducationService:
    @staticmethod
    def create_education(user_id: int, **data) -> int:
        """Create a new education entry with created_at/updated_at timestamps."""
        
    @staticmethod
    def list_user_educations(user_id: int) -> list[Education]:
        """Get all educations for a user."""
        
    @staticmethod
    def update_education(education_id: int, **updates) -> Education | None:
        """Update an education entry and set updated_at timestamp."""
        
    @staticmethod
    def delete_education(education_id: int) -> bool:
        """Delete an education entry."""
```

### UI Components

#### Onboarding Navigation
- Progress indicator showing current step (e.g., "Step 1 of 3")
- "Previous" and "Next" buttons for step navigation
- "Skip" option for Steps 2 and 3 (work experience and education)
- After Step 1 completion, user is created and redirected to home page

#### Form Validation
- Required field validation (first name, last name in Step 1)
- Optional field validation for Steps 2 and 3 (only if user chooses to add data)
- Date picker widgets for start/end dates (Streamlit date_input)
- Simple URL format validation (LinkedIn, GitHub, Website URLs)
- Basic email format validation
- Error handling: display errors and allow retry if user creation fails

#### User Page Redesign
- Replace `pages/users.py` with `pages/user.py`
- Single user profile view instead of user list
- Edit mode for updating user information (all metadata fields)
- Experience and education management sections (add/edit/delete)
- Save button that activates only when changes are made
- Display created_at and updated_at timestamps
- Use date picker widgets for date fields

### Session State Management
```python
# Onboarding state tracking
st.session_state.onboarding_step = 1
st.session_state.onboarding_data = {
    "user": {},
    "experiences": [],
    "educations": []
}
# Note: No onboarding_completed flag needed since completion is determined by user creation
```

### Implementation Strategy
1. Add new database tables for Experience and Education
2. Add new metadata fields to existing User table (phone, email, address, etc.)
3. Add created_at and updated_at fields to all models
4. Implement single-page onboarding flow
5. Update main navigation logic (check user existence, redirect appropriately)
6. Replace `pages/users.py` with `pages/user.py` for single user profile
7. Use Streamlit date pickers for all date inputs
8. Implement simple validation and error handling

### Success Criteria
- New users are automatically guided through onboarding on a single page
- User is created after Step 1 (basic information) completion
- Steps 2 and 3 (experience/education) are optional and can be skipped
- After onboarding, user is redirected to home page
- Onboarding page is hidden from navigation
- Existing users are redirected directly to home page (no users list)
- User page shows single user profile with all metadata fields editable
- Experience and education can be managed (add/edit/delete) on user page
- All timestamps (created_at/updated_at) are properly maintained
- Date pickers are used for all date inputs
- Simple validation and error handling with retry capability