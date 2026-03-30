"""models/attendance.py"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


VALID_STATUSES = {"Present", "Absent", "Late"}


@dataclass
class Attendance:
    enrollment_id: int
    date:          date
    status:        str     # "Present" | "Absent" | "Late"
    id:            Optional[int] = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status {self.status!r}. Must be one of {VALID_STATUSES}"
            )
