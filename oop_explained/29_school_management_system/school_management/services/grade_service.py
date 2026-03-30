"""services/grade_service.py"""

from __future__ import annotations

import logging
from datetime import date
from typing import List

from ..models       import Grade
from ..repositories import GradeRepository, EnrollmentRepository
from ..exceptions   import GradeError, EnrollmentNotFound

logger = logging.getLogger(__name__)


class GradeService:

    def __init__(self, config: dict) -> None:
        self._repo     = GradeRepository(config)
        self._enr_repo = EnrollmentRepository(config)

    def record(
        self,
        enrollment_id: int,
        exam_type:     str,
        marks:         float,
        total:         float,
        graded_on:     date | None = None,
    ) -> Grade:
        # Confirm enrollment exists
        self._enr_repo.get_by_id(enrollment_id)

        grade = Grade(
            enrollment_id = enrollment_id,
            exam_type     = exam_type,
            marks         = marks,
            total         = total,
            graded_on     = graded_on or date.today(),
        )
        return self._repo.add(grade)

    def get_for_enrollment(self, enrollment_id: int) -> List[Grade]:
        return self._repo.get_by_enrollment(enrollment_id)

    def average(self, enrollment_id: int) -> float:
        return self._repo.weighted_average(enrollment_id)

    def update(self, grade: Grade) -> None:
        if grade.id is None:
            raise GradeError("Cannot update a grade without an id.")
        self._repo.update(grade)

    def delete(self, grade_id: int) -> None:
        self._repo.delete(grade_id)
