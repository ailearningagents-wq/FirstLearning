"""
school_management/
  config.py         — DB config loaded from .env / environment variables
  exceptions.py     — Domain-specific exception hierarchy
  models/           — Pure-Python dataclasses (no DB dependency)
  db/               — Connection manager + DDL runner
  repositories/     — One repo class per table (CRUD)
  services/         — Business-logic layer (calls repositories)
  reports/          — Report generators (report card, roster, etc.)
  cli.py            — Interactive command-line interface
  seeder.py         — Populates the DB with sample/demo data
  tests/            — Pytest unit tests (mocked DB)
"""
