# School Management System
> **Production-ready Python + MySQL project** — Topic 29 of the `oop_explained` learning series.

---

## Project Structure

```
29_school_management_system/
├── run.py                          ← Entry point (CLI launcher / seeder)
├── requirements.txt                ← Runtime dependencies
├── requirements-dev.txt            ← Dev/test dependencies
├── .env.example                    ← Copy → .env and fill in DB credentials
├── .gitignore
│
├── school_management/              ← Main Python package
│   ├── __init__.py
│   ├── config.py                   ← .env / env-var loader
│   ├── exceptions.py               ← Custom exception hierarchy
│   ├── cli.py                      ← Interactive menu-driven CLI
│   ├── seeder.py                   ← Demo-data seeder
│   │
│   ├── models/                     ← Pure dataclass models (no DB)
│   │   ├── student.py
│   │   ├── teacher.py
│   │   ├── course.py
│   │   ├── enrollment.py
│   │   ├── grade.py
│   │   └── attendance.py
│   │
│   ├── db/                         ← Database layer
│   │   ├── connection.py           ← Context-manager connection wrapper
│   │   └── ddl.py                  ← CREATE TABLE IF NOT EXISTS statements
│   │
│   ├── repositories/               ← One class per table — pure CRUD
│   │   ├── student_repo.py
│   │   ├── teacher_repo.py
│   │   ├── course_repo.py
│   │   ├── enrollment_repo.py
│   │   ├── grade_repo.py
│   │   └── attendance_repo.py
│   │
│   ├── services/                   ← Business-logic layer
│   │   ├── student_service.py
│   │   ├── teacher_service.py
│   │   ├── course_service.py
│   │   ├── enrollment_service.py
│   │   ├── grade_service.py
│   │   └── attendance_service.py
│   │
│   └── reports/                    ← Report generators
│       ├── report_card.py
│       ├── course_roster.py
│       ├── teacher_summary.py
│       └── top_performers.py
│
└── tests/                          ← Pytest unit tests (no real DB needed)
    ├── test_models.py
    └── test_services.py
```

---

## Database Schema

```
students      id · name · email · dob · grade_level · enrolled_on
teachers      id · name · email · subject_specialisation · phone
courses       id · title · teacher_id(FK) · max_students · credits
enrollments   id · student_id(FK) · course_id(FK) · enrolled_on   [UNIQUE per pair]
grades        id · enrollment_id(FK) · exam_type · marks · total · graded_on
attendance    id · enrollment_id(FK) · date · status               [UNIQUE per day]
```

---

## Setup

### 1. MySQL

```sql
CREATE DATABASE school_db CHARACTER SET utf8mb4;
CREATE USER 'school_user'@'localhost' IDENTIFIED BY 'school_pass';
GRANT ALL PRIVILEGES ON school_db.* TO 'school_user'@'localhost';
FLUSH PRIVILEGES;
```

### 2. Python dependencies

```bash
cd 29_school_management_system
pip install -r requirements.txt          # production
pip install -r requirements-dev.txt      # + pytest for tests
```

### 3. Environment variables

```bash
cp .env.example .env
# Edit .env with your MySQL credentials
```

---

## Running the App

```bash
# Interactive CLI
python run.py

# Seed with 10 students, 5 teachers, 6 courses, grades & attendance
python run.py --seed

# Or run specific modules directly
python -m school_management.cli
python -m school_management.seeder
```

---

## Running Tests

```bash
cd 29_school_management_system
pytest tests/ -v
```

All tests are **fully mocked** — no MySQL connection required.

---

## Design Patterns Used

| Pattern | Where |
|---|---|
| **Repository** | `repositories/` — isolates all SQL from business logic |
| **Service Layer** | `services/` — enforces business rules, orchestrates repos |
| **Context Manager** | `db/connection.py` — auto-commit / rollback / close |
| **Facade** | `reports/` — simple interface over multiple services |
| **Dataclass + `__post_init__`** | `models/` — immutable-ish value objects with validation |

---

## Key Python Concepts Demonstrated

- **OOP**: Classes, inheritance, `@property`, `@dataclass`, `__post_init__`, `__str__`
- **Encapsulation**: Private `_repo` / `_cfg` attributes, no direct DB access from outside services
- **Exception hierarchy**: `SchoolError` base → domain-specific subclasses
- **Context managers**: `__enter__` / `__exit__` for safe connection lifecycle
- **Parameterised SQL**: All queries use `%s` placeholders — never f-strings — preventing SQL injection
- **Type hints**: Throughout, using `from __future__ import annotations`
- **`logging`**: Structured logging instead of `print()` in library code
- **`python-dotenv`**: Secrets loaded from `.env`, not hard-coded
