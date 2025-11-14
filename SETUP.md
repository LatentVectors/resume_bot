# Setup Guide

## Prerequisites

- **Node.js** >= 18.0.0
- **Python** >= 3.12
- **npm** (comes with Node.js)

## Initial Setup

Run this command from the project root to set up everything:

```bash
npm run setup
```

This will:

1. Install all Node.js dependencies for the monorepo
2. Create a Python virtual environment in `apps/api/.venv`
3. Install all Python dependencies including dev dependencies

## Manual Setup (if needed)

### Setup Python API only

```bash
npm run setup:api
```

Or manually:

```bash
cd apps/api
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -e '.[dev]'
```

### Setup Node.js dependencies only

```bash
npm install
```

## Development

### Run both API and Web simultaneously

```bash
npm run dev
```

This uses Turborepo to run both:

- **API**: `http://localhost:8000` (FastAPI with hot-reload)
- **Web**: `http://localhost:3000` (Next.js with hot-reload)

### Run Web only

```bash
npm run dev:web
```

### Run API only (from root)

```bash
cd apps/api
npm run dev
```

## Other Commands

### Build

```bash
npm run build
```

### Lint

```bash
npm run lint
```

### Test (API)

```bash
cd apps/api
npm run test
```

### Clean

Remove all generated files (keeps `.venv`):

```bash
npm run clean
```

Remove everything including virtual environment:

```bash
npm run clean:all
```

## Troubleshooting

### "uvicorn: command not found"

This means the Python virtual environment isn't set up. Run:

```bash
npm run setup:api
```

### "Missing packageManager field"

This has been fixed in `package.json`. Make sure you're using the latest version.

### Python version issues

Make sure you have Python 3.12 or higher:

```bash
python3 --version
```

If you need to install Python 3.12, use [pyenv](https://github.com/pyenv/pyenv) or download from [python.org](https://www.python.org/downloads/).
