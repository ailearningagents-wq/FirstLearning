"""models/teacher.py"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Teacher:
    name:                   str
    email:                  str
    subject_specialisation: str
    phone:                  str
    id:                     Optional[int] = field(default=None, repr=False)

    def __str__(self) -> str:
        return f"Teacher(id={self.id}, name={self.name!r}, subject={self.subject_specialisation!r})"

    def __post_init__(self) -> None:
        if "@" not in self.email:
            raise ValueError(f"Invalid email: {self.email!r}")
