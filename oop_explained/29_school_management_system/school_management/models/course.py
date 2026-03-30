"""models/course.py"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Course:
    title:        str
    teacher_id:   int
    max_students: int = 30
    credits:      int = 3
    id:           Optional[int] = field(default=None, repr=False)

    def __str__(self) -> str:
        return f"Course(id={self.id}, title={self.title!r}, credits={self.credits})"

    def __post_init__(self) -> None:
        if self.max_students < 1:
            raise ValueError("max_students must be >= 1")
        if self.credits < 1:
            raise ValueError("credits must be >= 1")
