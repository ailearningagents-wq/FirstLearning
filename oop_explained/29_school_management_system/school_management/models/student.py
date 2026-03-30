"""models/student.py"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class Student:
    name:        str
    email:       str
    dob:         date
    grade_level: int           # 1–12
    enrolled_on: date = field(default_factory=date.today)
    id:          Optional[int] = field(default=None, repr=False)

    # ── computed ─────────────────────────────────────────────────────
    def age(self) -> int:
        today = date.today()
        return today.year - self.dob.year - (
            (today.month, today.day) < (self.dob.month, self.dob.day)
        )

    def __str__(self) -> str:
        return f"Student(id={self.id}, name={self.name!r}, grade={self.grade_level})"

    def __post_init__(self) -> None:
        if not 1 <= self.grade_level <= 12:
            raise ValueError(f"grade_level must be 1–12, got {self.grade_level}")
        if "@" not in self.email:
            raise ValueError(f"Invalid email: {self.email!r}")
