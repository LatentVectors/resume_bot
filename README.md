# Resume Bot

An AI-powered application that turns a job description and your background into a polished, ATS-safe PDF resume. The application consists of a Next.js frontend and a FastAPI backend, providing a streamlined onboarding flow to capture your profile, generate tailored resumes in seconds, preview and download PDFs, and experiment with HTML templates powered by an LLM.

## Highlights
- **Generate customized resumes**: Rapidly generate tailored resumes to a target job description.
- **Template lab**: Generate personalized ATS-safe resume templates.
- **Local storage**: Uses SQLite by default; no external DB required.
- **Modern architecture**: Next.js frontend with FastAPI backend for scalability and extensibility.

## Repository Structure

The project is organized as a monorepo with separate packages:

```
resume/
├── packages/
│   ├── api/              # FastAPI backend (Python)
│   │   ├── api/          # API routes, schemas, services
│   │   ├── src/          # Core logic, agents, features
│   │   ├── app/          # Streamlit app (deprecated, will be removed)
│   │   ├── tests/        # Python tests
│   │   ├── pyproject.toml
│   │   └── .env          # Backend environment variables
│   └── web/              # Next.js frontend (TypeScript/React)
│       ├── src/
│       │   ├── app/      # Next.js App Router pages
│       │   ├── components/  # React components
│       │   ├── lib/      # Utilities, API client, config
│       │   └── types/    # TypeScript types
│       ├── package.json
│       └── .env.local    # Frontend environment variables
├── .agents/              # Development specs
├── __notes__/            # Development notes
└── README.md             # This file
```

## Prerequisites

### Backend
- Python 3.12+
- macOS/Linux/Windows

### Frontend
- Node.js 18+ and npm/pnpm/yarn

### API Keys
- OpenRouter API key (for LLM features)
- Optional: LangSmith API key (for tracing and debugging)

## Quickstart

### 1. Clone the Repository

```bash
git clone https://github.com/<your-org-or-user>/resume.git
cd resume
```

### 2. Backend Setup

1. Navigate to the API directory:
```bash
cd packages/api
```

2. Create and activate a virtual environment:
```bash
python3.12 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -U pip
pip install -e .[dev]
```

4. Configure environment:
   - Copy `.env.example` to `.env` in `packages/api/`:
   ```bash
   cp .env.example .env
   ```
   - Edit `.env` and fill in your API keys (see [Environment Configuration](#environment-configuration) below).

### 3. Frontend Setup

1. Navigate to the web directory:
```bash
cd packages/web
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment:
   - Create `.env.local` in `packages/web/`:
   ```bash
   echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
   ```

### 4. Running the Application

**Backend (FastAPI):**

In one terminal:
```bash
cd packages/api
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uvicorn api.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
- API docs: `http://localhost:8000/api/docs`
- Health check: `http://localhost:8000/api/health`

**Frontend (Next.js):**

In another terminal:
```bash
cd packages/web
npm run dev
```

The frontend will be available at `http://localhost:3000`

**Optional: Run Both Services Together**

You can use the `concurrently` script to run both services from the web directory:

```bash
cd packages/web
npm run dev:all
```

This requires adding the script to `package.json` (see [Development Workflow](#development-workflow) below).

## Environment Configuration

### Backend Environment Variables (`packages/api/.env`)

Key variables (see `.env.example` for complete list):

- `OPENROUTER_API_KEY` — **Required** for LLM features (resume generation, template chat).
- `DATABASE_URL` — Database connection string (defaults to SQLite: `sqlite:///data/resume_bot.db`).
- `CORS_ORIGINS` — Comma-separated list of allowed CORS origins (defaults to `http://localhost:3000,http://localhost:8501`).
- `CORS_ORIGIN_REGEX` — Regex pattern for matching CORS origins (defaults to `https://.*\.vercel\.app` for Vercel preview deployments).

**Example `.env` for production:**
```bash
OPENROUTER_API_KEY=your-key-here
CORS_ORIGINS=http://localhost:3000,https://yourapp.vercel.app
CORS_ORIGIN_REGEX=https://.*\.vercel\.app
```

### Frontend Environment Variables (`packages/web/.env.local`)

- `NEXT_PUBLIC_API_URL` — Backend API URL (defaults to `http://localhost:8000`).

**For production:**
```bash
NEXT_PUBLIC_API_URL=https://api.yourdomain.com
```

## Type Generation

The frontend uses TypeScript types generated from the FastAPI OpenAPI specification.

**To generate types:**

1. Ensure the FastAPI backend is running on port 8000.
2. Run the type generation script:
```bash
cd packages/web
npm run generate:types
```

This will generate/update `packages/web/src/types/api.ts` with TypeScript types matching your API schemas.

**When to regenerate:**
- After making changes to API schemas or routes
- When adding new endpoints or modifying request/response models
- Before starting frontend development after backend changes

## Development Workflow

### Running Services Independently

Each service runs independently from its own directory:

**Backend:**
```bash
cd packages/api
source .venv/bin/activate
uvicorn api.main:app --reload --port 8000
```

**Frontend:**
```bash
cd packages/web
npm run dev
```

### Running Both Services Together (Optional)

Add to `packages/web/package.json`:

```json
{
  "scripts": {
    "dev": "next dev",
    "dev:all": "concurrently \"npm run dev\" \"npm run dev:api\"",
    "dev:api": "cd ../api && source .venv/bin/activate && uvicorn api.main:app --reload --port 8000"
  }
}
```

Then run:
```bash
cd packages/web
npm run dev:all
```

**Note:** The `dev:api` script assumes a Unix-like shell. For Windows, you may need to adjust the activation command.

## Using the Application

### Onboarding
When you first launch the app, you'll be guided through creating your profile:
- **Basic info**: name, contact, and links
- **Experience (optional)**: roles, dates, and descriptions
- **Education (optional)**: schools and degrees
- **Certificates (optional)**: professional certifications

### Home Page
- Paste a job description and submit
- Navigate to the job intake workflow

### Job Intake Workflow
A multi-step process:
1. **Details**: Enter job title, company, and description
2. **Experience**: Select relevant experiences and generate resume
3. **Proposals**: Review and accept/reject AI-generated experience proposals

### Jobs Page
- View all saved jobs
- Filter by status and favorites
- Navigate to job detail pages

### Job Detail Page
View and manage individual jobs with tabs:
- **Overview**: Job details, edit information, toggle favorite, update status
- **Resume**: View resume versions, generate new versions, download PDFs
- **Cover Letter**: View cover letter versions, generate new versions, download PDFs
- **Notes**: Add and edit job notes

### Profile Page
- Review and edit your profile information
- Manage experiences, education, and certificates
- Add, edit, or remove entries at any time

## Troubleshooting

### Backend Issues

- **"OpenRouter API key is not set"**: Ensure `OPENROUTER_API_KEY` is present in `packages/api/.env`
- **Port 8000 already in use**: Stop other FastAPI instances or change the port: `uvicorn api.main:app --reload --port 8001`
- **Database errors**: Check that the database file exists and has write permissions. Default location: `packages/api/data/resume_bot.db`
- **CORS errors**: Verify `CORS_ORIGINS` in `.env` includes your frontend URL (e.g., `http://localhost:3000`)

### Frontend Issues

- **API connection errors**: Verify `NEXT_PUBLIC_API_URL` in `.env.local` matches your backend URL
- **Type errors**: Regenerate types with `npm run generate:types` (ensure backend is running)
- **Port 3000 already in use**: Stop other Next.js instances or change the port: `npm run dev -- -p 3001`

### General

- **PDFs not appearing**: Confirm files exist under `packages/api/data/resumes/` and that the app has write permissions
- **Template preview issues**: If LLM output contains fenced code, the app auto-cleans fences; retry if rendering fails

## Development

### Backend Development

- Linting/type checks: Configured via Ruff/Mypy in `packages/api/pyproject.toml`
- Project code lives under `packages/api/src/` and `packages/api/api/`
- Run tests: `cd packages/api && pytest`

### Frontend Development

- Linting: ESLint configured in `packages/web/eslint.config.mjs`
- Type checking: TypeScript configured in `packages/web/tsconfig.json`
- Code formatting: Prettier (if configured)

## Deployment

### Frontend (Vercel)

1. Connect your GitHub repository to Vercel
2. Set `NEXT_PUBLIC_API_URL` environment variable to your deployed API URL
3. Deploy automatically on push to main branch

### Backend

Deploy FastAPI to a service that supports long-running processes (e.g., LangServ, AWS Lambda with appropriate timeout, Railway, Render).

**Important:** Configure CORS to allow your Vercel domain:
```bash
CORS_ORIGINS=https://yourapp.vercel.app
CORS_ORIGIN_REGEX=https://.*\.vercel\.app
```

## Architecture Notes

- **Backend**: FastAPI with SQLModel/SQLite, LangGraph agents for LLM workflows
- **Frontend**: Next.js 14+ with App Router, React Query for data fetching, Zustand for client state
- **Type Safety**: TypeScript types generated from FastAPI OpenAPI schema
- **UI**: ShadCN UI components with Tailwind CSS

## Future Enhancements

- Supabase authentication and database migration
- Browser extension integration
- Templates page (deferred)
- Responses page (deferred)
- Testing infrastructure (Jest, React Testing Library, Playwright)

## License

MIT (or your preferred license).
