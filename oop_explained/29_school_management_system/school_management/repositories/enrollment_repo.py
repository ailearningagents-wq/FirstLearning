"""repositories/enrollment_repo.py — CRUD for the `enrollments` table."""

from __future__ import annotations

import logging
from datetime import date
from typing import List

from ..db.connection import DatabaseConnection, MySQLError
from ..exceptions    import EnrollmentError, EnrollmentNotFound
from ..models        import Enrollment

logger = logging.getLogger(__name__)


class EnrollmentRepository:

    def __init__(self, config: dict) -> None:
        self._cfg = config

    def add(self, enrollment: Enrollment) -> Enrollment:
        sql = """
            INSERT INTO enrollments (student_id, course_id, enrolled_on)
            VALUES (%s, %s, %s)
        """
        try:
            with DatabaseConnection(self._cfg) as db:
                db.execute(sql, (
                    enrollment.student_id,
                    enrollment.course_id,
                    enrollment.enrolled_on,
                ))
                enrollment.id = db.lastrowid
        except MySQLError as exc:
            if "uq_enrollment" in str(exc).lower() or "1062" in str(exc):
                raise EnrollmentError(
                    f"Student {enrollment.student_id} is already enrolled "
                    f"in course {enrollment.course_id}."
                ) from exc
            raise
        logger.info("Enrolled student=%d in course=%d",
                    enrollment.student_id, enrollment.course_id)
        return enrollment

    def get_by_id(self, enrollment_id: int) -> Enrollment:
        with DatabaseConnection(self._cfg) as db:
            row = db.fetchone(
                "SELECT * FROM enrollments WHERE id = %s", (enrollment_id,)
            )
        if not row:
            raise EnrollmentNotFound(f"No enrollment with id={enrollment_id}")
        return self._from_row(row)

    def get_by_student_and_course(
        self, student_id: int, course_id: int
    ) -> Enrollment:
        with DatabaseConnection(self._cfg) as db:
            row = db.fetchone(
                "SELECT * FROM enrollments WHERE student_id=%s AND course_id=%s",
                (student_id, course_id),
            )
        if not row:
            raise EnrollmentNotFound(
                f"No enrollment for student={student_id}, course={course_id}"
            )
        return self._from_row(row)

    def courses_for_student(self, student_id: int) -> List[dict]:
        """Return enriched rows (enrollment_id, course details, teacher name)."""
        sql = """
            SELECT e.id          AS enrollment_id,
                   c.id          AS course_id,
                   c.title       AS course_title,
                   c.credits,
                   t.name        AS teacher_name
            FROM   enrollments e
            JOIN   courses  c ON c.id = e.course_id
            JOIN   teachers t ON t.id = c.teacher_id
            WHERE  e.student_id = %s
            ORDER  BY c.title
        """
        with DatabaseConnection(self._cfg) as db:
            return db.fetchall(sql, (student_id,))

    def students_in_course(self, course_id: int) -> List[dict]:
        """Return enriched rows (enrollment_id + student details)."""
        sql = """
            SELECT e.id          AS enrollment_id,
                   s.id          AS student_id,
                   s.name,
                   s.email,
                   s.grade_level,
                   e.enrolled_on
            FROM   enrollments e
            JOIN   students s ON s.id = e.student_id
            WHERE  e.course_id = %s
            ORDER  BY s.name
        """
        with DatabaseConnection(self._cfg) as db:
            return db.fetchall(sql, (course_id,))

    def delete(self, student_id: int, course_id: int) -> None:
        with DatabaseConnection(self._cfg) as db:
            db.execute(
                "DELETE FROM enrollments WHERE student_id=%s AND course_id=%s",
                (student_id, course_id),
            )
        logger.info("Unenrolled student=%d from course=%d", student_id, course_id)

    @staticmethod
    def _from_row(row: dict) -> Enrollment:
        return Enrollment(
            id          = row["id"],
            student_id  = row["student_id"],
            course_id   = row["course_id"],
            enrolled_on = row["enrolled_on"],
        )
