#!/usr/bin/env python3
"""Simple script to run the Streamlit app."""

import sys
from pathlib import Path

import streamlit.web.cli as stcli


def main():
    """Run the Streamlit application."""
    app_path = Path(__file__).parent / "app" / "main.py"

    sys.argv = ["streamlit", "run", str(app_path)]
    sys.exit(stcli.main())


if __name__ == "__main__":
    main()
