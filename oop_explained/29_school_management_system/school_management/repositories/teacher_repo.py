"""repositories/teacher_repo.py — CRUD for the `teachers` table."""

from __future__ import annotations

import logging
from typing import List

from ..db.connection import DatabaseConnection
from ..exceptions    import TeacherNotFound
from ..models        import Teacher

logger = logging.getLogger(__name__)


class TeacherRepository:

    def __init__(self, config: dict) -> None:
        self._cfg = config

    def add(self, teacher: Teacher) -> Teacher:
        sql = """
            INSERT INTO teachers (name, email, subject_specialisation, phone)
            VALUES (%s, %s, %s, %s)
        """
        with DatabaseConnection(self._cfg) as db:
            db.execute(sql, (
                teacher.name, teacher.email,
                teacher.subject_specialisation, teacher.phone,
            ))
            teacher.id = db.lastrowid
        logger.info("Added %s", teacher)
        return teacher

    def get_by_id(self, teacher_id: int) -> Teacher:
        with DatabaseConnection(self._cfg) as db:
            row = db.fetchone("SELECT * FROM teachers WHERE id = %s", (teacher_id,))
        if not row:
            raise TeacherNotFound(f"No teacher with id={teacher_id}")
        return self._from_row(row)

    def get_by_email(self, email: str) -> Teacher:
        with DatabaseConnection(self._cfg) as db:
            row = db.fetchone("SELECT * FROM teachers WHERE email = %s", (email,))
        if not row:
            raise TeacherNotFound(f"No teacher with email={email!r}")
        return self._from_row(row)

    def get_all(self) -> List[Teacher]:
        with DatabaseConnection(self._cfg) as db:
            rows = db.fetchall("SELECT * FROM teachers ORDER BY name")
        return [self._from_row(r) for r in rows]

    def update(self, teacher: Teacher) -> None:
        if teacher.id is None:
            raise TeacherNotFound("Cannot update a teacher without an id.")
        sql = """
            UPDATE teachers
            SET name=%s, email=%s, subject_specialisation=%s, phone=%s
            WHERE id=%s
        """
        with DatabaseConnection(self._cfg) as db:
            db.execute(sql, (
                teacher.name, teacher.email,
                teacher.subject_specialisation, teacher.phone, teacher.id,
            ))
        logger.info("Updated %s", teacher)

    def delete(self, teacher_id: int) -> None:
        with DatabaseConnection(self._cfg) as db:
            db.execute("DELETE FROM teachers WHERE id = %s", (teacher_id,))
        logger.info("Deleted teacher id=%d", teacher_id)

    @staticmethod
    def _from_row(row: dict) -> Teacher:
        return Teacher(
            id                     = row["id"],
            name                   = row["name"],
            email                  = row["email"],
            subject_specialisation = row["subject_specialisation"],
            phone                  = row["phone"],
        )
