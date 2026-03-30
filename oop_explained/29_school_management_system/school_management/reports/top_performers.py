"""reports/top_performers.py — Ranked list of top students in a course."""

from __future__ import annotations

from ..models    import Grade
from ..services  import CourseService, EnrollmentService, GradeService


def print_top_performers(
    course_id:      int,
    top_n:          int,
    course_svc:     CourseService,
    enrollment_svc: EnrollmentService,
    grade_svc:      GradeService,
) -> None:
    course   = course_svc.get(course_id)
    students = enrollment_svc.students_in_course(course_id)

    ranked = sorted(
        [(s["name"], grade_svc.average(s["enrollment_id"])) for s in students],
        key=lambda x: x[1],
        reverse=True,
    )

    print(f"\n  TOP {top_n} PERFORMERS — {course.title}")
    print("  " + "─" * 40)
    if not ranked:
        print("  (No data yet)\n")
        return

    for rank, (name, pct) in enumerate(ranked[:top_n], 1):
        letter = Grade(enrollment_id=0, exam_type="", marks=pct, total=100).letter_grade
        print(f"  {rank}.  {name:<26} {pct:6.2f}%  [{letter}]")
    print()
