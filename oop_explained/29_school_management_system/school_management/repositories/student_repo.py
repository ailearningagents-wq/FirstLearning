"""repositories/student_repo.py — CRUD for the `students` table."""

from __future__ import annotations

import logging
from datetime import date
from typing import List, Optional

from ..db.connection import DatabaseConnection
from ..exceptions    import StudentNotFound
from ..models        import Student

logger = logging.getLogger(__name__)


class StudentRepository:
    """All database operations that touch the `students` table."""

    def __init__(self, config: dict) -> None:
        self._cfg = config

    # ── CREATE ───────────────────────────────────────────────────────
    def add(self, student: Student) -> Student:
        sql = """
            INSERT INTO students (name, email, dob, grade_level, enrolled_on)
            VALUES (%s, %s, %s, %s, %s)
        """
        with DatabaseConnection(self._cfg) as db:
            db.execute(sql, (
                student.name, student.email, student.dob,
                student.grade_level, student.enrolled_on,
            ))
            student.id = db.lastrowid
        logger.info("Added %s", student)
        return student

    # ── READ ─────────────────────────────────────────────────────────
    def get_by_id(self, student_id: int) -> Student:
        with DatabaseConnection(self._cfg) as db:
            row = db.fetchone("SELECT * FROM students WHERE id = %s", (student_id,))
        if not row:
            raise StudentNotFound(f"No student with id={student_id}")
        return self._from_row(row)

    def get_by_email(self, email: str) -> Student:
        with DatabaseConnection(self._cfg) as db:
            row = db.fetchone("SELECT * FROM students WHERE email = %s", (email,))
        if not row:
            raise StudentNotFound(f"No student with email={email!r}")
        return self._from_row(row)

    def get_all(self, grade_level: Optional[int] = None) -> List[Student]:
        if grade_level is not None:
            sql, params = (
                "SELECT * FROM students WHERE grade_level = %s ORDER BY name",
                (grade_level,),
            )
        else:
            sql, params = "SELECT * FROM students ORDER BY name", ()
        with DatabaseConnection(self._cfg) as db:
            rows = db.fetchall(sql, params)
        return [self._from_row(r) for r in rows]

    def search_by_name(self, fragment: str) -> List[Student]:
        """Case-insensitive partial name search."""
        with DatabaseConnection(self._cfg) as db:
            rows = db.fetchall(
                "SELECT * FROM students WHERE name LIKE %s ORDER BY name",
                (f"%{fragment}%",),
            )
        return [self._from_row(r) for r in rows]

    def count(self) -> int:
        with DatabaseConnection(self._cfg) as db:
            row = db.fetchone("SELECT COUNT(*) AS cnt FROM students")
        return row["cnt"] if row else 0

    # ── UPDATE ───────────────────────────────────────────────────────
    def update(self, student: Student) -> None:
        if student.id is None:
            raise StudentNotFound("Cannot update a student without an id.")
        sql = """
            UPDATE students
            SET name=%s, email=%s, dob=%s, grade_level=%s
            WHERE id=%s
        """
        with DatabaseConnection(self._cfg) as db:
            db.execute(sql, (
                student.name, student.email,
                student.dob, student.grade_level, student.id,
            ))
        logger.info("Updated %s", student)

    # ── DELETE ───────────────────────────────────────────────────────
    def delete(self, student_id: int) -> None:
        with DatabaseConnection(self._cfg) as db:
            db.execute("DELETE FROM students WHERE id = %s", (student_id,))
        logger.info("Deleted student id=%d", student_id)

    # ── HELPER ───────────────────────────────────────────────────────
    @staticmethod
    def _from_row(row: dict) -> Student:
        return Student(
            id          = row["id"],
            name        = row["name"],
            email       = row["email"],
            dob         = row["dob"],
            grade_level = row["grade_level"],
            enrolled_on = row["enrolled_on"],
        )
