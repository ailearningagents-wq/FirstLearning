"""services/teacher_service.py"""

from __future__ import annotations

import logging
from typing import List

from ..models       import Teacher
from ..repositories import TeacherRepository

logger = logging.getLogger(__name__)


class TeacherService:

    def __init__(self, config: dict) -> None:
        self._repo = TeacherRepository(config)

    def hire(self, name: str, email: str, subject: str, phone: str) -> Teacher:
        teacher = Teacher(name=name, email=email,
                          subject_specialisation=subject, phone=phone)
        return self._repo.add(teacher)

    def get(self, teacher_id: int) -> Teacher:
        return self._repo.get_by_id(teacher_id)

    def get_by_email(self, email: str) -> Teacher:
        return self._repo.get_by_email(email)

    def list_all(self) -> List[Teacher]:
        return self._repo.get_all()

    def update(self, teacher: Teacher) -> None:
        self._repo.update(teacher)

    def remove(self, teacher_id: int) -> None:
        self._repo.delete(teacher_id)
