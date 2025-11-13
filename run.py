#!/usr/bin/env python3
"""Run both FastAPI backend and Streamlit frontend."""

from __future__ import annotations

import multiprocessing
import sys
from pathlib import Path

import streamlit.web.cli as stcli
import uvicorn

from src.config import settings


def main() -> None:
    """Run the FastAPI backend and Streamlit frontend concurrently."""
    streamlit_process = multiprocessing.Process(target=run_streamlit, name="streamlit-runner", daemon=True)
    streamlit_process.start()

    try:
        run_api()
    except KeyboardInterrupt:
        # Allow Ctrl+C to stop both services without a traceback.
        pass
    finally:
        streamlit_process.terminate()
        streamlit_process.join()


def run_api() -> None:
    """Run FastAPI backend in the main process so uvicorn reload works."""
    uvicorn.run(
        "api.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level="info",
    )


def run_streamlit() -> None:
    """Run Streamlit frontend in a separate process."""
    app_path = Path(__file__).parent / "app" / "main.py"
    sys.argv = ["streamlit", "run", str(app_path)]
    stcli.main()


if __name__ == "__main__":
    main()
