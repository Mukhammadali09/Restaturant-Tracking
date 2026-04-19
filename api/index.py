"""Vercel serverless entry point.

Vercel's Python runtime imports `app` from this file and wraps it as a
serverless function. All the real logic lives in the top-level `app.py`.
"""

import os
import sys

# Make the project root importable (models, config, seed, etc.)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app  # noqa: E402

# `app` is already created as a module-level Flask instance in app.py.
# Re-calling create_app() would double-initialize SQLAlchemy and break requests.
