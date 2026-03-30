"""services/course_service.py"""

from __future__ import annotations

import logging
from typing import List

from ..models       import Course
from ..repositories import CourseRepository, TeacherRepository
from ..exceptions   import TeacherNotFound

logger = logging.getLogger(__name__)


class CourseService:

    def __init__(self, config: dict) -> None:
        self._repo         = CourseRepository(config)
        self._teacher_repo = TeacherRepository(config)

    def create(
        self,
        title:        str,
        teacher_id:   int,
        max_students: int = 30,
        credits:      int = 3,
    ) -> Course:
        # Ensure the teacher exists before creating the course
        self._teacher_repo.get_by_id(teacher_id)   # raises TeacherNotFound if bad
        course = Course(title=title, teacher_id=teacher_id,
                        max_students=max_students, credits=credits)
        return self._repo.add(course)

    def get(self, course_id: int) -> Course:
        return self._repo.get_by_id(course_id)

    def list_all(self) -> List[Course]:
        return self._repo.get_all()

    def list_by_teacher(self, teacher_id: int) -> List[Course]:
        return self._repo.get_by_teacher(teacher_id)

    def update(self, course: Course) -> None:
        self._repo.update(course)

    def remove(self, course_id: int) -> None:
        self._repo.delete(course_id)

    def available_seats(self, course_id: int) -> int:
        course   = self._repo.get_by_id(course_id)
        enrolled = self._repo.enrolled_count(course_id)
        return max(0, course.max_students - enrolled)
