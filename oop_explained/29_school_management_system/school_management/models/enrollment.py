"""models/enrollment.py"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Enrollment:
    student_id:  int
    course_id:   int
    enrolled_on: date = field(default_factory=date.today)
    id:          Optional[int] = field(default=None, repr=False)

    def __str__(self) -> str:
        return (f"Enrollment(id={self.id}, student={self.student_id}, "
                f"course={self.course_id})")
