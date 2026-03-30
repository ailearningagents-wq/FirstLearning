"""repositories/course_repo.py — CRUD for the `courses` table."""

from __future__ import annotations

import logging
from typing import List

from ..db.connection import DatabaseConnection
from ..exceptions    import CourseNotFound
from ..models        import Course

logger = logging.getLogger(__name__)


class CourseRepository:

    def __init__(self, config: dict) -> None:
        self._cfg = config

    def add(self, course: Course) -> Course:
        sql = """
            INSERT INTO courses (title, teacher_id, max_students, credits)
            VALUES (%s, %s, %s, %s)
        """
        with DatabaseConnection(self._cfg) as db:
            db.execute(sql, (
                course.title, course.teacher_id,
                course.max_students, course.credits,
            ))
            course.id = db.lastrowid
        logger.info("Added %s", course)
        return course

    def get_by_id(self, course_id: int) -> Course:
        with DatabaseConnection(self._cfg) as db:
            row = db.fetchone("SELECT * FROM courses WHERE id = %s", (course_id,))
        if not row:
            raise CourseNotFound(f"No course with id={course_id}")
        return self._from_row(row)

    def get_all(self) -> List[Course]:
        with DatabaseConnection(self._cfg) as db:
            rows = db.fetchall("SELECT * FROM courses ORDER BY title")
        return [self._from_row(r) for r in rows]

    def get_by_teacher(self, teacher_id: int) -> List[Course]:
        with DatabaseConnection(self._cfg) as db:
            rows = db.fetchall(
                "SELECT * FROM courses WHERE teacher_id = %s ORDER BY title",
                (teacher_id,),
            )
        return [self._from_row(r) for r in rows]

    def update(self, course: Course) -> None:
        if course.id is None:
            raise CourseNotFound("Cannot update a course without an id.")
        sql = """
            UPDATE courses
            SET title=%s, teacher_id=%s, max_students=%s, credits=%s
            WHERE id=%s
        """
        with DatabaseConnection(self._cfg) as db:
            db.execute(sql, (
                course.title, course.teacher_id,
                course.max_students, course.credits, course.id,
            ))
        logger.info("Updated %s", course)

    def delete(self, course_id: int) -> None:
        with DatabaseConnection(self._cfg) as db:
            db.execute("DELETE FROM courses WHERE id = %s", (course_id,))
        logger.info("Deleted course id=%d", course_id)

    def enrolled_count(self, course_id: int) -> int:
        with DatabaseConnection(self._cfg) as db:
            row = db.fetchone(
                "SELECT COUNT(*) AS cnt FROM enrollments WHERE course_id = %s",
                (course_id,),
            )
        return row["cnt"] if row else 0

    @staticmethod
    def _from_row(row: dict) -> Course:
        return Course(
            id           = row["id"],
            title        = row["title"],
            teacher_id   = row["teacher_id"],
            max_students = row["max_students"],
            credits      = row["credits"],
        )
