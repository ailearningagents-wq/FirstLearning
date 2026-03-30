"""models/grade.py"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


VALID_EXAM_TYPES = {"Quiz", "Midterm", "Final", "Assignment", "Lab", "Project"}


@dataclass
class Grade:
    enrollment_id: int
    exam_type:     str    # one of VALID_EXAM_TYPES
    marks:         float
    total:         float  # maximum possible marks
    graded_on:     date = field(default_factory=date.today)
    id:            Optional[int] = field(default=None, repr=False)

    # ── computed properties ───────────────────────────────────────────
    @property
    def percentage(self) -> float:
        return round((self.marks / self.total) * 100, 2) if self.total else 0.0

    @property
    def letter_grade(self) -> str:
        p = self.percentage
        if p >= 90: return "A+"
        if p >= 80: return "A"
        if p >= 70: return "B"
        if p >= 60: return "C"
        if p >= 50: return "D"
        return "F"

    def __str__(self) -> str:
        return (f"Grade(enrollment={self.enrollment_id}, {self.exam_type}: "
                f"{self.marks}/{self.total} = {self.percentage}% [{self.letter_grade}])")

    def __post_init__(self) -> None:
        if self.total <= 0:
            raise ValueError("total marks must be > 0")
        if not (0 <= self.marks <= self.total):
            raise ValueError(
                f"marks ({self.marks}) must be between 0 and total ({self.total})"
            )
