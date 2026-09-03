"""
Shared pytest configuration. Ensures the backend package root is importable
regardless of which directory `pytest` is invoked from, and defaults to a
throwaway SQLite URL so these unit tests never require a live Postgres
instance (none of them execute real queries, but importing
`database.session` does construct an Engine at import time).
"""
import os
import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_local.db")
