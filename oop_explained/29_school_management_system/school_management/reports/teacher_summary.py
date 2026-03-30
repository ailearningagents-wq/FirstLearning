"""reports/teacher_summary.py — Workload summary for all teachers."""

from __future__ import annotations

from ..db.connection import DatabaseConnection
from ..services      import TeacherService


def print_teacher_summary(
    teacher_svc: TeacherService,
    config:      dict,
) -> None:
    teachers = teacher_svc.list_all()

    print("\n" + "═" * 64)
    print("  TEACHER WORKLOAD SUMMARY")
    print("═" * 64)
    print(f"  {'Name':<26} {'Subject':<22} {'Courses':>8} {'Students':>9}")
    print("  " + "─" * 66)

    sql = """
        SELECT COUNT(DISTINCT c.id)         AS num_courses,
               COUNT(DISTINCT e.student_id) AS num_students
        FROM   courses c
        LEFT JOIN enrollments e ON e.course_id = c.id
        WHERE  c.teacher_id = %s
    """
    for teacher in teachers:
        with DatabaseConnection(config) as db:
            row = db.fetchone(sql, (teacher.id,))
        nc = row["num_courses"]  if row else 0
        ns = row["num_students"] if row else 0
        print(f"  {teacher.name:<26} {teacher.subject_specialisation:<22}"
              f" {nc:>8} {ns:>9}")
    print()
