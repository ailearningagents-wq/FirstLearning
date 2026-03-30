"""
cli.py — Interactive command-line interface for the School Management System.

Run:
    python -m school_management.cli
    # or from the project root:
    python cli.py

Menu structure:
  1  Students   → list / add / update / delete / search
  2  Teachers   → list / add / update / delete
  3  Courses    → list / add / update / delete
  4  Enroll     → enroll / unenroll student in course
  5  Grades     → record / view grades
  6  Attendance → mark / view attendance
  7  Reports    → report card / roster / teacher summary / top performers
  0  Exit
"""

from __future__ import annotations

import logging
import sys
from datetime import date

from .config     import get_db_config, LOG_LEVEL
from .db         import setup_database
from .services   import (
    StudentService, TeacherService, CourseService,
    EnrollmentService, GradeService, AttendanceService,
)
from .reports    import (
    print_report_card, print_course_roster,
    print_teacher_summary, print_top_performers,
)
from .exceptions import SchoolError
from .db.connection import MYSQL_AVAILABLE

# ── Logging setup ─────────────────────────────────────────────────────────────
logging.basicConfig(
    level   = getattr(logging, LOG_LEVEL, logging.INFO),
    format  = "%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

SEP = "─" * 56


def _input(prompt: str) -> str:
    """Wrapper around input() that strips whitespace."""
    return input(prompt).strip()


def _int_input(prompt: str) -> int:
    while True:
        try:
            return int(_input(prompt))
        except ValueError:
            print("  Please enter a valid integer.")


def _date_input(prompt: str) -> date:
    while True:
        raw = _input(f"{prompt} (YYYY-MM-DD): ")
        try:
            return date.fromisoformat(raw)
        except ValueError:
            print("  Invalid date. Use YYYY-MM-DD format.")


def _float_input(prompt: str) -> float:
    while True:
        try:
            return float(_input(prompt))
        except ValueError:
            print("  Please enter a valid number.")


# ══════════════════════════════════════════════════════════════════
# SUB-MENUS
# ══════════════════════════════════════════════════════════════════

def menu_students(svc: StudentService) -> None:
    while True:
        print(f"\n  STUDENTS\n  {SEP}")
        print("  1  List all students")
        print("  2  Add student")
        print("  3  View student")
        print("  4  Update student")
        print("  5  Delete student")
        print("  6  Search by name")
        print("  0  Back")
        choice = _input("  Choice: ")

        if choice == "1":
            students = svc.list_all()
            if not students:
                print("  No students found.")
            for s in students:
                print(f"  {s.id:>4}  {s.name:<25}  Grade {s.grade_level}  {s.email}")

        elif choice == "2":
            name   = _input("  Name        : ")
            email  = _input("  Email       : ")
            dob    = _date_input("  Date of Birth")
            grade  = _int_input("  Grade Level : ")
            try:
                s = svc.register(name, email, dob, grade)
                print(f"  Registered: {s}")
            except (SchoolError, ValueError) as e:
                print(f"  Error: {e}")

        elif choice == "3":
            sid = _int_input("  Student ID: ")
            try:
                s = svc.get(sid)
                print(f"\n  {s}")
                print(f"  Email: {s.email}  |  DOB: {s.dob}  |  Age: {s.age()}")
            except SchoolError as e:
                print(f"  Error: {e}")

        elif choice == "4":
            sid = _int_input("  Student ID to update: ")
            try:
                s = svc.get(sid)
                print(f"  Current: {s}")
                s.name        = _input(f"  New name       [{s.name}]: ") or s.name
                s.email       = _input(f"  New email      [{s.email}]: ") or s.email
                grade_in      = _input(f"  New grade lvl  [{s.grade_level}]: ")
                s.grade_level = int(grade_in) if grade_in else s.grade_level
                svc.update(s)
                print("  Updated.")
            except (SchoolError, ValueError) as e:
                print(f"  Error: {e}")

        elif choice == "5":
            sid  = _int_input("  Student ID to delete: ")
            conf = _input("  Confirm delete? (yes/no): ").lower()
            if conf == "yes":
                svc.remove(sid)
                print("  Deleted.")
            else:
                print("  Cancelled.")

        elif choice == "6":
            frag     = _input("  Name fragment: ")
            results  = svc.search(frag)
            if not results:
                print("  No matches.")
            for s in results:
                print(f"  {s.id:>4}  {s.name:<25}  Grade {s.grade_level}")

        elif choice == "0":
            break
        else:
            print("  Unknown option.")


def menu_teachers(svc: TeacherService) -> None:
    while True:
        print(f"\n  TEACHERS\n  {SEP}")
        print("  1  List all teachers")
        print("  2  Hire teacher")
        print("  3  Update teacher")
        print("  4  Delete teacher")
        print("  0  Back")
        choice = _input("  Choice: ")

        if choice == "1":
            for t in svc.list_all():
                print(f"  {t.id:>4}  {t.name:<25}  {t.subject_specialisation}")

        elif choice == "2":
            name    = _input("  Name           : ")
            email   = _input("  Email          : ")
            subject = _input("  Subject        : ")
            phone   = _input("  Phone          : ")
            try:
                t = svc.hire(name, email, subject, phone)
                print(f"  Hired: {t}")
            except (SchoolError, ValueError) as e:
                print(f"  Error: {e}")

        elif choice == "3":
            tid = _int_input("  Teacher ID to update: ")
            try:
                t = svc.get(tid)
                t.name                   = _input(f"  Name    [{t.name}]: ")         or t.name
                t.email                  = _input(f"  Email   [{t.email}]: ")        or t.email
                t.subject_specialisation = _input(f"  Subject [{t.subject_specialisation}]: ") or t.subject_specialisation
                t.phone                  = _input(f"  Phone   [{t.phone}]: ")        or t.phone
                svc.update(t)
                print("  Updated.")
            except SchoolError as e:
                print(f"  Error: {e}")

        elif choice == "4":
            tid  = _int_input("  Teacher ID to delete: ")
            conf = _input("  Confirm? (yes/no): ").lower()
            if conf == "yes":
                try:
                    svc.remove(tid)
                    print("  Deleted.")
                except SchoolError as e:
                    print(f"  Error: {e}")

        elif choice == "0":
            break


def menu_courses(svc: CourseService) -> None:
    while True:
        print(f"\n  COURSES\n  {SEP}")
        print("  1  List all courses")
        print("  2  Create course")
        print("  3  Update course")
        print("  4  Delete course")
        print("  5  Available seats")
        print("  0  Back")
        choice = _input("  Choice: ")

        if choice == "1":
            for c in svc.list_all():
                print(f"  {c.id:>4}  {c.title:<30}  Credits: {c.credits}"
                      f"  Max: {c.max_students}  Teacher ID: {c.teacher_id}")

        elif choice == "2":
            title       = _input("  Title         : ")
            teacher_id  = _int_input("  Teacher ID    : ")
            max_st      = _int_input("  Max students  : ")
            credits     = _int_input("  Credits       : ")
            try:
                c = svc.create(title, teacher_id, max_st, credits)
                print(f"  Created: {c}")
            except (SchoolError, ValueError) as e:
                print(f"  Error: {e}")

        elif choice == "3":
            cid = _int_input("  Course ID to update: ")
            try:
                c = svc.get(cid)
                c.title        = _input(f"  Title       [{c.title}]: ")        or c.title
                ms             = _input(f"  Max students [{c.max_students}]: ")
                c.max_students = int(ms) if ms else c.max_students
                cr             = _input(f"  Credits      [{c.credits}]: ")
                c.credits      = int(cr) if cr else c.credits
                svc.update(c)
                print("  Updated.")
            except (SchoolError, ValueError) as e:
                print(f"  Error: {e}")

        elif choice == "4":
            cid  = _int_input("  Course ID to delete: ")
            conf = _input("  Confirm? (yes/no): ").lower()
            if conf == "yes":
                svc.remove(cid)
                print("  Deleted.")

        elif choice == "5":
            cid   = _int_input("  Course ID: ")
            seats = svc.available_seats(cid)
            print(f"  Available seats: {seats}")

        elif choice == "0":
            break


def menu_enrollment(svc: EnrollmentService) -> None:
    while True:
        print(f"\n  ENROLLMENT\n  {SEP}")
        print("  1  Enroll student")
        print("  2  Unenroll student")
        print("  3  Courses for student")
        print("  4  Students in course")
        print("  0  Back")
        choice = _input("  Choice: ")

        if choice == "1":
            sid = _int_input("  Student ID: ")
            cid = _int_input("  Course ID : ")
            try:
                e = svc.enroll(sid, cid)
                print(f"  Enrolled (enrollment id={e.id})")
            except SchoolError as e_:
                print(f"  Error: {e_}")

        elif choice == "2":
            sid = _int_input("  Student ID: ")
            cid = _int_input("  Course ID : ")
            svc.unenroll(sid, cid)
            print("  Unenrolled.")

        elif choice == "3":
            sid  = _int_input("  Student ID: ")
            rows = svc.courses_for_student(sid)
            if not rows:
                print("  Not enrolled in any course.")
            for r in rows:
                print(f"  Enrollment {r['enrollment_id']:>4}  {r['course_title']:<28}"
                      f"  Credits: {r['credits']}  Teacher: {r['teacher_name']}")

        elif choice == "4":
            cid  = _int_input("  Course ID: ")
            rows = svc.students_in_course(cid)
            if not rows:
                print("  No students enrolled.")
            for r in rows:
                print(f"  Enrollment {r['enrollment_id']:>4}  {r['name']:<25}"
                      f"  Grade {r['grade_level']}")

        elif choice == "0":
            break


def menu_grades(svc: GradeService) -> None:
    while True:
        print(f"\n  GRADES\n  {SEP}")
        print("  1  Record grade")
        print("  2  View grades for enrollment")
        print("  3  Average for enrollment")
        print("  0  Back")
        choice = _input("  Choice: ")

        if choice == "1":
            enr_id    = _int_input("  Enrollment ID : ")
            exam_type = _input("  Exam type (Quiz/Midterm/Final/Assignment): ")
            marks     = _float_input("  Marks obtained: ")
            total     = _float_input("  Total marks   : ")
            try:
                g = svc.record(enr_id, exam_type, marks, total)
                print(f"  Recorded: {g}")
            except (SchoolError, ValueError) as e:
                print(f"  Error: {e}")

        elif choice == "2":
            enr_id = _int_input("  Enrollment ID: ")
            grades = svc.get_for_enrollment(enr_id)
            if not grades:
                print("  No grades recorded.")
            for g in grades:
                print(f"  [{g.id}] {g.exam_type:<14} {g.marks:6.1f}/{g.total:6.1f}"
                      f"  {g.percentage}%  [{g.letter_grade}]")

        elif choice == "3":
            enr_id = _int_input("  Enrollment ID: ")
            avg    = svc.average(enr_id)
            print(f"  Weighted average: {avg}%")

        elif choice == "0":
            break


def menu_attendance(svc: AttendanceService) -> None:
    while True:
        print(f"\n  ATTENDANCE\n  {SEP}")
        print("  1  Mark attendance")
        print("  2  View attendance for enrollment")
        print("  3  Attendance rate")
        print("  0  Back")
        choice = _input("  Choice: ")

        if choice == "1":
            enr_id  = _int_input("  Enrollment ID : ")
            att_date = _date_input("  Date")
            status  = _input("  Status (Present/Absent/Late): ")
            try:
                svc.mark(enr_id, att_date, status)
                print("  Marked.")
            except (SchoolError, ValueError) as e:
                print(f"  Error: {e}")

        elif choice == "2":
            enr_id  = _int_input("  Enrollment ID: ")
            records = svc.get_for_enrollment(enr_id)
            if not records:
                print("  No records.")
            for r in records:
                print(f"  {r.date}  {r.status}")

        elif choice == "3":
            enr_id = _int_input("  Enrollment ID: ")
            rate   = svc.rate(enr_id)
            print(f"  Attendance rate: {rate}%")

        elif choice == "0":
            break


def menu_reports(
    student_svc:    StudentService,
    teacher_svc:    TeacherService,
    course_svc:     CourseService,
    enrollment_svc: EnrollmentService,
    grade_svc:      GradeService,
    attendance_svc: AttendanceService,
    config:         dict,
) -> None:
    while True:
        print(f"\n  REPORTS\n  {SEP}")
        print("  1  Report card (student)")
        print("  2  Course roster")
        print("  3  Teacher workload summary")
        print("  4  Top performers (course)")
        print("  0  Back")
        choice = _input("  Choice: ")

        if choice == "1":
            sid = _int_input("  Student ID: ")
            try:
                print_report_card(sid, student_svc, enrollment_svc,
                                  grade_svc, attendance_svc)
            except SchoolError as e:
                print(f"  Error: {e}")

        elif choice == "2":
            cid = _int_input("  Course ID: ")
            try:
                print_course_roster(cid, course_svc, enrollment_svc)
            except SchoolError as e:
                print(f"  Error: {e}")

        elif choice == "3":
            print_teacher_summary(teacher_svc, config)

        elif choice == "4":
            cid   = _int_input("  Course ID: ")
            top_n = _int_input("  Top N    : ")
            try:
                print_top_performers(cid, top_n, course_svc,
                                     enrollment_svc, grade_svc)
            except SchoolError as e:
                print(f"  Error: {e}")

        elif choice == "0":
            break


# ══════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════

def main() -> None:
    print("""
╔══════════════════════════════════════════════════════════════╗
║       SCHOOL MANAGEMENT SYSTEM  —  Interactive CLI           ║
╚══════════════════════════════════════════════════════════════╝
""")

    if not MYSQL_AVAILABLE:
        print("  ERROR: mysql-connector-python is not installed.")
        print("  Run:   pip install mysql-connector-python")
        sys.exit(1)

    config = get_db_config()
    try:
        setup_database(config)
    except Exception as exc:
        print(f"\n  Cannot connect to MySQL: {exc}")
        print("  Check .env / environment variables and try again.")
        sys.exit(1)

    # Instantiate all services once
    student_svc    = StudentService(config)
    teacher_svc    = TeacherService(config)
    course_svc     = CourseService(config)
    enrollment_svc = EnrollmentService(config)
    grade_svc      = GradeService(config)
    attendance_svc = AttendanceService(config)

    while True:
        print(f"\n  MAIN MENU\n  {SEP}")
        print("  1  Students")
        print("  2  Teachers")
        print("  3  Courses")
        print("  4  Enrollment")
        print("  5  Grades")
        print("  6  Attendance")
        print("  7  Reports")
        print("  0  Exit")
        choice = _input("  Choice: ")

        if   choice == "1":
            menu_students(student_svc)
        elif choice == "2":
            menu_teachers(teacher_svc)
        elif choice == "3":
            menu_courses(course_svc)
        elif choice == "4":
            menu_enrollment(enrollment_svc)
        elif choice == "5":
            menu_grades(grade_svc)
        elif choice == "6":
            menu_attendance(attendance_svc)
        elif choice == "7":
            menu_reports(student_svc, teacher_svc, course_svc,
                         enrollment_svc, grade_svc, attendance_svc, config)
        elif choice == "0":
            print("  Goodbye!")
            break
        else:
            print("  Unknown option — try again.")


if __name__ == "__main__":
    main()
