"""repositories/attendance_repo.py — CRUD for the `attendance` table."""

from __future__ import annotations

import logging
from datetime import date
from typing import List

from ..db.connection import DatabaseConnection
from ..exceptions    import AttendanceError
from ..models        import Attendance
from ..models.attendance import VALID_STATUSES

logger = logging.getLogger(__name__)


class AttendanceRepository:

    def __init__(self, config: dict) -> None:
        self._cfg = config

    def mark(self, enrollment_id: int, att_date: date, status: str) -> Attendance:
        if status not in VALID_STATUSES:
            raise AttendanceError(
                f"Invalid status {status!r}. Must be one of {VALID_STATUSES}"
            )
        # Upsert: update if the record for that day already exists
        sql = """
            INSERT INTO attendance (enrollment_id, date, status)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE status = VALUES(status)
        """
        with DatabaseConnection(self._cfg) as db:
            db.execute(sql, (enrollment_id, att_date, status))
            att_id = db.lastrowid or 0
        rec = Attendance(id=att_id, enrollment_id=enrollment_id,
                         date=att_date, status=status)
        logger.info("Marked attendance: %s", rec)
        return rec

    def get_for_enrollment(self, enrollment_id: int) -> List[Attendance]:
        sql = """
            SELECT * FROM attendance
            WHERE enrollment_id = %s
            ORDER BY date
        """
        with DatabaseConnection(self._cfg) as db:
            rows = db.fetchall(sql, (enrollment_id,))
        return [
            Attendance(
                id=r["id"], enrollment_id=r["enrollment_id"],
                date=r["date"], status=r["status"],
            )
            for r in rows
        ]

    def attendance_rate(self, enrollment_id: int) -> float:
        """Percentage of days marked Present or Late."""
        records = self.get_for_enrollment(enrollment_id)
        if not records:
            return 0.0
        attended = sum(1 for r in records if r.status in ("Present", "Late"))
        return round((attended / len(records)) * 100, 2)

    def delete(self, enrollment_id: int, att_date: date) -> None:
        with DatabaseConnection(self._cfg) as db:
            db.execute(
                "DELETE FROM attendance WHERE enrollment_id=%s AND date=%s",
                (enrollment_id, att_date),
            )
