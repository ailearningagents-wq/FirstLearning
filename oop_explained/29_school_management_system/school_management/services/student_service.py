"""
services/student_service.py — Business-logic layer for students.

The service layer sits between the CLI/API and the repositories.
It validates business rules and orchestrates calls to one or more repos.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import List, Optional

from ..models        import Student
from ..repositories  import StudentRepository

logger = logging.getLogger(__name__)


class StudentService:

    def __init__(self, config: dict) -> None:
        self._repo = StudentRepository(config)

    def register(
        self,
        name:        str,
        email:       str,
        dob:         date,
        grade_level: int,
    ) -> Student:
        """Create and persist a new student."""
        student = Student(name=name, email=email, dob=dob, grade_level=grade_level)
        return self._repo.add(student)

    def get(self, student_id: int) -> Student:
        return self._repo.get_by_id(student_id)

    def get_by_email(self, email: str) -> Student:
        return self._repo.get_by_email(email)

    def list_all(self, grade_level: Optional[int] = None) -> List[Student]:
        return self._repo.get_all(grade_level)

    def search(self, name_fragment: str) -> List[Student]:
        return self._repo.search_by_name(name_fragment)

    def update(self, student: Student) -> None:
        self._repo.update(student)

    def remove(self, student_id: int) -> None:
        """Delete student and all related enrollments/grades (CASCADE)."""
        self._repo.delete(student_id)

    def total_count(self) -> int:
        return self._repo.count()
