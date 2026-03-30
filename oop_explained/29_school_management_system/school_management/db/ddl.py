"""
db/ddl.py — DDL statements and database setup helper.

Run setup_database(config) once to create all tables.
"""

from __future__ import annotations

import logging

from .connection import DatabaseConnection

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# TABLE DEFINITIONS
# Ordered so foreign-key references always point to already-created tables.
# ─────────────────────────────────────────────────────────────────────────────
_DDL: list[str] = [
    # ── students ─────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS students (
        id           INT          AUTO_INCREMENT PRIMARY KEY,
        name         VARCHAR(120) NOT NULL,
        email        VARCHAR(200) NOT NULL UNIQUE,
        dob          DATE         NOT NULL,
        grade_level  TINYINT      NOT NULL,
        enrolled_on  DATE         NOT NULL DEFAULT (CURRENT_DATE),
        CONSTRAINT chk_grade CHECK (grade_level BETWEEN 1 AND 12)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ── teachers ─────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS teachers (
        id                     INT          AUTO_INCREMENT PRIMARY KEY,
        name                   VARCHAR(120) NOT NULL,
        email                  VARCHAR(200) NOT NULL UNIQUE,
        subject_specialisation VARCHAR(100) NOT NULL,
        phone                  VARCHAR(20)  NOT NULL
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ── courses ──────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS courses (
        id           INT          AUTO_INCREMENT PRIMARY KEY,
        title        VARCHAR(150) NOT NULL,
        teacher_id   INT          NOT NULL,
        max_students SMALLINT     NOT NULL DEFAULT 30,
        credits      TINYINT      NOT NULL DEFAULT 3,
        FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE RESTRICT
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ── enrollments ──────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS enrollments (
        id          INT  AUTO_INCREMENT PRIMARY KEY,
        student_id  INT  NOT NULL,
        course_id   INT  NOT NULL,
        enrolled_on DATE NOT NULL DEFAULT (CURRENT_DATE),
        UNIQUE KEY uq_enrollment (student_id, course_id),
        FOREIGN KEY (student_id) REFERENCES students(id)  ON DELETE CASCADE,
        FOREIGN KEY (course_id)  REFERENCES courses(id)   ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ── grades ───────────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS grades (
        id            INT           AUTO_INCREMENT PRIMARY KEY,
        enrollment_id INT           NOT NULL,
        exam_type     VARCHAR(50)   NOT NULL,
        marks         DECIMAL(7,2)  NOT NULL,
        total         DECIMAL(7,2)  NOT NULL,
        graded_on     DATE          NOT NULL DEFAULT (CURRENT_DATE),
        FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,

    # ── attendance ───────────────────────────────────────────────────────────
    """
    CREATE TABLE IF NOT EXISTS attendance (
        id            INT  AUTO_INCREMENT PRIMARY KEY,
        enrollment_id INT  NOT NULL,
        date          DATE NOT NULL,
        status        ENUM('Present','Absent','Late') NOT NULL DEFAULT 'Present',
        UNIQUE KEY uq_attendance (enrollment_id, date),
        FOREIGN KEY (enrollment_id) REFERENCES enrollments(id) ON DELETE CASCADE
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
    """,
]


def setup_database(config: dict) -> None:
    """
    Create all schema tables if they do not already exist.
    Safe to call on every startup (idempotent).
    """
    logger.info("Running database setup (CREATE TABLE IF NOT EXISTS)...")
    with DatabaseConnection(config) as db:
        for stmt in _DDL:
            db.execute(stmt.strip())
    logger.info("Database setup complete.")
