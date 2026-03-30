"""reports/report_card.py — Per-student academic report card."""

from __future__ import annotations

from ..models  import Grade
from ..services import (
    StudentService, EnrollmentService,
    GradeService, AttendanceService,
)


def print_report_card(
    student_id:        int,
    student_svc:       StudentService,
    enrollment_svc:    EnrollmentService,
    grade_svc:         GradeService,
    attendance_svc:    AttendanceService,
) -> None:
    student = student_svc.get(student_id)
    courses = enrollment_svc.courses_for_student(student_id)

    print("\n" + "═" * 64)
    print(f"  REPORT CARD — {student.name.upper()}")
    print(f"  Student ID: {student.id}   Grade Level: {student.grade_level}"
          f"   Age: {student.age()}")
    print("═" * 64)

    if not courses:
        print("  (No courses enrolled)\n")
        return

    for row in courses:
        enr_id  = row["enrollment_id"]
        avg_pct = grade_svc.average(enr_id)
        att_pct = attendance_svc.rate(enr_id)
        letter  = Grade(enrollment_id=enr_id, exam_type="",
                        marks=avg_pct, total=100).letter_grade

        print(f"\n  Course     : {row['course_title']}")
        print(f"  Teacher    : {row['teacher_name']}")
        print(f"  Credits    : {row['credits']}")
        print(f"  Average    : {avg_pct:6.2f}%  [{letter}]")
        print(f"  Attendance : {att_pct:5.2f}%")
        print("  " + "─" * 44)

        for g in grade_svc.get_for_enrollment(enr_id):
            print(f"    {g.exam_type:<15} {g.marks:6.1f} / {g.total:6.1f}"
                  f"  ({g.percentage}%)  [{g.letter_grade}]")

    print("\n" + "═" * 64 + "\n")
