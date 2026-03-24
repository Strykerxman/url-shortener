"""
Root conftest: bootstrap environment variables before any app module is imported.

pytest loads this file BEFORE tests/conftest.py, so setting os.environ here
at module level guarantees the vars are present when tests/conftest.py does
`from app.main import app`.
"""

import os

# These defaults are safe test values (SQLite, localhost).
# Real values live in .env / .env.local (never committed).
os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("BASE_URL", "http://testserver")
os.environ.setdefault("ENV_NAME", "test")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
