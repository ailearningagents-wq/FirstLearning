"""
services/enrollment_service.py — Enrollment business logic.

Business rules enforced:
  1. A student cannot enroll in the same course twice.
  2. A course cannot exceed its max_students capacity.
  3. A student must exist; a course must exist.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import List

from ..models       import Enrollment
from ..repositories import (
    EnrollmentRepository, StudentRepository,
    CourseRepository,
)
from ..exceptions   import EnrollmentError

logger = logging.getLogger(__name__)


class EnrollmentService:

    def __init__(self, config: dict) -> None:
        self._repo         = EnrollmentRepository(config)
        self._student_repo = StudentRepository(config)
        self._course_repo  = CourseRepository(config)

    def enroll(self, student_id: int, course_id: int) -> Enrollment:
        # Validate student & course exist (repos raise *NotFound on miss)
        self._student_repo.get_by_id(student_id)
        course = self._course_repo.get_by_id(course_id)

        # Capacity check
        enrolled = self._course_repo.enrolled_count(course_id)
        if enrolled >= course.max_students:
            raise EnrollmentError(
                f"Course '{course.title}' is at full capacity "
                f"({enrolled}/{course.max_students})."
            )

        enr = Enrollment(student_id=student_id, course_id=course_id,
                         enrolled_on=date.today())
        return self._repo.add(enr)  # repo raises EnrollmentError for duplicate

    def unenroll(self, student_id: int, course_id: int) -> None:
        self._repo.delete(student_id, course_id)

    def courses_for_student(self, student_id: int) -> List[dict]:
        return self._repo.courses_for_student(student_id)

    def students_in_course(self, course_id: int) -> List[dict]:
        return self._repo.students_in_course(course_id)

    def get_enrollment(self, student_id: int, course_id: int) -> Enrollment:
        return self._repo.get_by_student_and_course(student_id, course_id)
