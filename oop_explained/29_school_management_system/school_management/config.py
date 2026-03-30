"""
config.py — Load database settings from .env or environment variables.

Priority:  actual env-var  >  .env file  >  hard-coded default
"""

from __future__ import annotations

import os
from pathlib import Path

# Load .env if present (requires python-dotenv)
try:
    from dotenv import load_dotenv
    _env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(_env_path)
except ImportError:
    pass  # python-dotenv not installed; rely solely on real env vars


def get_db_config() -> dict:
    """Return a mysql-connector-python compatible connection dict."""
    return {
        "host":       os.environ.get("SCHOOL_DB_HOST",   "localhost"),
        "port":       int(os.environ.get("SCHOOL_DB_PORT", "3306")),
        "user":       os.environ.get("SCHOOL_DB_USER",   "school_user"),
        "password":   os.environ.get("SCHOOL_DB_PASS",   "school_pass"),
        "database":   os.environ.get("SCHOOL_DB_NAME",   "school_db"),
        "charset":    "utf8mb4",
        "autocommit": False,
        "use_pure":   True,
    }


LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO").upper()
