# Resume Bot

An AI‑powered Streamlit application that turns a job description and your background into a polished, ATS‑safe PDF resume. It provides a streamlined onboarding flow to capture your profile, lets you generate tailored resumes in seconds, preview and download PDFs, and experiment with HTML templates powered by an LLM.

## Highlights
- **Generate customized resumes**: Rapidly generate tailored resumes to a target job description.
- **Template lab**: Generate personalized ATS-safe resume templates.
- **Local storage**: Uses SQLite by default; no external DB required.

## Architecture (at a glance)
- Streamlit app entry: `app/main.py`, launcher: `run.py`
- Pages: `app/pages/` (`_onboarding.py`, `home.py`, `jobs.py`, `templates.py`, `user.py`)
- Services & DB: `app/services/`, `src/database.py` (SQLModel + SQLite), `src/config.py`
- AI workflow: `src/generate_resume.py`, `src/agents/main/*` (LangGraph nodes and state)
- Templates: `src/features/resume/templates/*.html` + LLM generator in `src/features/resume/`

## Prerequisites
- Python 3.12+
- macOS/Linux/Windows
- An OpenAI API key to enable LLM-powered features

## Quickstart
1) Clone the repo
```bash
git clone https://github.com/<your-org-or-user>/resume.git
cd resume
```

2) Create and activate a virtual environment
```bash
python3.12 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
```

3) Install dependencies
```bash
pip install -U pip
pip install -e .[dev]
```

4) Configure environment
- Copy `.env.example` to `.env` and fill in values (see details below).
```bash
cp .env.example .env
```

5) Run the Streamlit app
```bash
python run.py
```
Streamlit will print a local URL such as `http://localhost:8501`. Open it in your browser.

## Environment Configuration
Configuration is managed with Pydantic Settings (`src/config.py`) and loaded from `.env` if present.

Key variables (see `.env.example`):
- `OPENAI_API_KEY` — required for LLM features (resume generation, template chat).

Notes:
- Data directory defaults to `data/`; PDFs are written to `data/resumes/`.
- Logs are written to `log/` and rotated automatically.

## Using the App
When you first launch, the app checks if a user exists and will guide you through onboarding if needed.

### Onboarding
Create your profile in three quick steps:
- **Basic info**: name, contact, and links.
- **Experience (optional)**: roles, dates, and descriptions.
- **Education (optional)**: schools and degrees.

Once complete, you’ll land on the main app with your profile saved.

### Home
- Paste a job description and click **Generate Resume**.
- The app runs an agentic workflow to tailor your content and produce a PDF.
- A preview renders inline; download the file or jump to the Jobs page.

### Jobs
- View a table of all generated resumes tied to job descriptions.
- Click **View** to open a dialog with the full description and embedded PDF.
- Download the PDF directly from the table or the dialog.

### Templates
- Use a chat-like interface to generate or edit clean, ATS‑safe HTML templates with an LLM.
- Each response creates a new version; navigate versions, preview as PDF, and download HTML.

### Profile
- Review and edit your saved profile details.
- Add, edit, or remove experiences and education entries at any time.

## CLI Utilities (optional)
A small CLI exists under `src/features/resume/cli.py` for working with templates and sample renders.

- Generate PDF samples for all built-in templates (uses dummy data):
```bash
python -m src.features.resume.cli generate
```

- Generate a new template with the LLM and optional image guidance, saving HTML (and optional PDF preview) under `data/templates/generated/`:
```bash
python -m src.features.resume.cli new-template "Clean ATS-safe single-column resume" --pdf
```

## Troubleshooting
- "OpenAI API key is not set": Ensure `OPENAI_API_KEY` is present in `.env` and your shell session.
- Port already in use: Stop other Streamlit instances or run `streamlit run app/main.py --server.port 8502`.
- PDFs not appearing: Confirm files exist under `data/resumes/` and that the app has write permissions.
- Template preview issues: If LLM output contains fenced code, the app auto-cleans fences; retry if rendering fails.

## Development
- Linting/type checks are configured via Ruff/Mypy in `pyproject.toml`.
- Project code lives under `src/` (added to the wheel in build config).

## License
MIT (or your preferred license).
