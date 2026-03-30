"""reports/course_roster.py — List of students enrolled in a course."""

from __future__ import annotations

from ..services import CourseService, EnrollmentService


def print_course_roster(
    course_id:      int,
    course_svc:     CourseService,
    enrollment_svc: EnrollmentService,
) -> None:
    course   = course_svc.get(course_id)
    students = enrollment_svc.students_in_course(course_id)

    print("\n" + "═" * 64)
    print(f"  COURSE ROSTER — {course.title.upper()}")
    print(f"  ID: {course.id}   Max: {course.max_students}"
          f"   Enrolled: {len(students)}"
          f"   Available seats: {course_svc.available_seats(course_id)}")
    print("═" * 64)

    if not students:
        print("  (No students enrolled)\n")
        return

    print(f"  {'#':<4} {'Name':<26} {'Grade':<8} {'Email':<28} Enrolled On")
    print("  " + "─" * 75)
    for i, s in enumerate(students, 1):
        print(f"  {i:<4} {s['name']:<26} {s['grade_level']:<8}"
              f" {s['email']:<28} {s['enrolled_on']}")
    print()
