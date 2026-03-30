"""repositories/grade_repo.py — CRUD for the `grades` table."""

from __future__ import annotations

import logging
from typing import List

from ..db.connection import DatabaseConnection
from ..models        import Grade

logger = logging.getLogger(__name__)


class GradeRepository:

    def __init__(self, config: dict) -> None:
        self._cfg = config

    def add(self, grade: Grade) -> Grade:
        # Validation already done in Grade.__post_init__
        sql = """
            INSERT INTO grades (enrollment_id, exam_type, marks, total, graded_on)
            VALUES (%s, %s, %s, %s, %s)
        """
        with DatabaseConnection(self._cfg) as db:
            db.execute(sql, (
                grade.enrollment_id, grade.exam_type,
                grade.marks, grade.total, grade.graded_on,
            ))
            grade.id = db.lastrowid
        logger.info("Added %s", grade)
        return grade

    def get_by_enrollment(self, enrollment_id: int) -> List[Grade]:
        sql = """
            SELECT * FROM grades
            WHERE enrollment_id = %s
            ORDER BY graded_on, exam_type
        """
        with DatabaseConnection(self._cfg) as db:
            rows = db.fetchall(sql, (enrollment_id,))
        return [self._from_row(r) for r in rows]

    def get_by_id(self, grade_id: int) -> Grade:
        with DatabaseConnection(self._cfg) as db:
            row = db.fetchone("SELECT * FROM grades WHERE id = %s", (grade_id,))
        if not row:
            raise ValueError(f"No grade with id={grade_id}")
        return self._from_row(row)

    def weighted_average(self, enrollment_id: int) -> float:
        """Weighted average percentage (total marks / total max * 100)."""
        grades = self.get_by_enrollment(enrollment_id)
        if not grades:
            return 0.0
        total_earned = sum(g.marks for g in grades)
        total_max    = sum(g.total  for g in grades)
        return round((total_earned / total_max) * 100, 2) if total_max else 0.0

    def update(self, grade: Grade) -> None:
        sql = "UPDATE grades SET marks=%s, total=%s, exam_type=%s WHERE id=%s"
        with DatabaseConnection(self._cfg) as db:
            db.execute(sql, (grade.marks, grade.total, grade.exam_type, grade.id))
        logger.info("Updated grade id=%d", grade.id)

    def delete(self, grade_id: int) -> None:
        with DatabaseConnection(self._cfg) as db:
            db.execute("DELETE FROM grades WHERE id = %s", (grade_id,))
        logger.info("Deleted grade id=%d", grade_id)

    @staticmethod
    def _from_row(row: dict) -> Grade:
        return Grade(
            id            = row["id"],
            enrollment_id = row["enrollment_id"],
            exam_type     = row["exam_type"],
            marks         = float(row["marks"]),
            total         = float(row["total"]),
            graded_on     = row["graded_on"],
        )
