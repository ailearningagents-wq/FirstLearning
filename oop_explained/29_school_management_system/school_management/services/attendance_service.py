"""services/attendance_service.py"""

from __future__ import annotations

import logging
from datetime import date
from typing import List

from ..models       import Attendance
from ..repositories import AttendanceRepository, EnrollmentRepository

logger = logging.getLogger(__name__)


class AttendanceService:

    def __init__(self, config: dict) -> None:
        self._repo     = AttendanceRepository(config)
        self._enr_repo = EnrollmentRepository(config)

    def mark(
        self,
        enrollment_id: int,
        att_date:      date,
        status:        str,
    ) -> Attendance:
        # Confirm enrollment exists before marking
        self._enr_repo.get_by_id(enrollment_id)
        return self._repo.mark(enrollment_id, att_date, status)

    def get_for_enrollment(self, enrollment_id: int) -> List[Attendance]:
        return self._repo.get_for_enrollment(enrollment_id)

    def rate(self, enrollment_id: int) -> float:
        """Attendance rate as a percentage (Present + Late count)."""
        return self._repo.attendance_rate(enrollment_id)
