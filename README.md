# Resume Bot

AI-powered resume generation system built with Python, Streamlit, and LangGraph.

## Features

- 🤖 LangGraph-powered workflow for resume generation
- 📄 Modern Streamlit web interface with multi-page navigation
- 🗄️ SQLite database for user management
- 🔧 Type checking with mypy and linting with ruff
- 🧪 Comprehensive test suite with pytest

## Project Structure

```
resume-bot/
├── src/                    # Core business logic
│   ├── config.py          # Configuration management
│   ├── database.py        # Database models and operations
│   └── workflow.py        # LangGraph workflow
├── app/                   # Streamlit application
│   ├── main.py           # Main app entry point
│   ├── pages/            # Streamlit pages
│   │   ├── home.py       # Home page
│   │   └── users.py      # User management page
│   └── services/         # Business logic services
│       └── resume_service.py
├── tests/                # Test suite
├── data/                 # Local data storage (not in repo)
└── pyproject.toml        # Project configuration
```

## Setup

### Prerequisites

- Python 3.12+
- uv package manager

### Installation

1. **Clone and navigate to the project:**
   ```bash
   cd /Users/mjlindow/projects/resume
   ```

2. **Create and activate virtual environment:**
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install the project in editable mode:**
   ```bash
   uv pip install -e .
   ```

4. **Install development dependencies:**
   ```bash
   uv pip install -e ".[dev]"
   ```

5. **Set up environment variables:**
   ```bash
   cp .example.env .env
   # Edit .env with your API keys
   ```

6. **Initialize the database:**
   The database will be created automatically when you first run the app.

## Running the Application

### Streamlit App

**Option 1: Direct command**
```bash
streamlit run app/main.py
```

**Option 2: Using the run script**
```bash
python run.py
```

The app will be available at `http://localhost:8501`

### Development Commands

**Type checking:**
```bash
mypy src/ app/
```

**Linting and formatting:**
```bash
ruff check src/ app/
ruff format src/ app/
```

**Running tests:**
```bash
pytest
```

## Usage

1. **Home Page**: Enter your requirements and click "Generate Resume" to test the LangGraph workflow
2. **Users Page**: Add and manage users in the system

## Key Features Explained

### Import Structure

The project uses a proper package structure where:
- `src/` contains the core business logic
- `app/` contains the Streamlit application
- The project is installed in editable mode, allowing clean imports like `from src.workflow import resume_workflow`

### LangGraph Integration

The workflow in `src/workflow.py` demonstrates:
- Simple state management with `WorkflowState`
- Basic node creation and workflow compilation
- Easy extensibility for more complex resume generation logic

### Database Management

- SQLite database with Pydantic models
- Automatic database initialization
- Clean separation between models and operations

### Streamlit Architecture

- Multi-page structure for scalability
- Service layer for business logic
- Clean separation of concerns between UI and backend

## Development

### Adding New Features

1. **New LangGraph nodes**: Add to `src/workflow.py`
2. **New database models**: Add to `src/database.py`
3. **New Streamlit pages**: Add to `app/pages/`
4. **New services**: Add to `app/services/`

### Testing

All tests are in the `tests/` directory. Run with:
```bash
pytest -v
```

## Configuration

Edit `.env` file for:
- Database URL
- API keys for LangChain/OpenAI
- App settings

## Next Steps

- Expand the LangGraph workflow with actual resume generation
- Add more sophisticated UI components
- Implement user authentication
- Add resume templates and customization options
