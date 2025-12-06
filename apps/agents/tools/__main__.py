"""Allow running tools as a module: python -m tools"""

from .cli import app

if __name__ == "__main__":
    app()
