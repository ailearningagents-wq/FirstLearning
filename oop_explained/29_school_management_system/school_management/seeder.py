"""
seeder.py — Populates the database with realistic demo data.

Safe to run multiple times: existing rows (matched by email / title) are
skipped rather than re-inserted, so re-running will not create duplicates.

Usage:
    python -m school_management.seeder
    # or
    python seeder.py
"""

from __future__ import annotations

import logging
import random
import sys
from datetime import date, timedelta

from .config     import get_db_config
from .db         import setup_database
from .services   import (
    StudentService, TeacherService, CourseService,
    EnrollmentService, GradeService, AttendanceService,
)
from .exceptions import EnrollmentError, SchoolError
from .db.connection import MYSQL_AVAILABLE

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    format="%(levelname)-8s %(message)s")


# ─────────────────────────────────────────────────────────────────────────────
# SEED DATA
# ─────────────────────────────────────────────────────────────────────────────

TEACHERS = [
    ("Dr. Priya Sharma",    "priya@school.edu",    "Mathematics",     "9876543210"),
    ("Mr. Rahul Verma",     "rahul@school.edu",    "Physics",         "9123456780"),
    ("Ms. Anita Nair",      "anita@school.edu",    "Computer Science","9988776655"),
    ("Prof. Suresh Patel",  "suresh@school.edu",   "Chemistry",       "9001122334"),
    ("Mrs. Deepa Menon",    "deepa@school.edu",    "English",         "9445566778"),
]

# (title, teacher_email, max_students, credits)
COURSES = [
    ("Algebra II",          "priya@school.edu",    30, 4),
    ("Calculus",            "priya@school.edu",    25, 5),
    ("Physics Mechanics",   "rahul@school.edu",    30, 4),
    ("Python Programming",  "anita@school.edu",    20, 3),
    ("Organic Chemistry",   "suresh@school.edu",   28, 4),
    ("English Literature",  "deepa@school.edu",    35, 3),
]

# (name, email, dob, grade_level)
STUDENTS = [
    ("Alice Johnson",   "alice@school.edu",    date(2009, 3, 12),  10),
    ("Bob Kumar",       "bob@school.edu",       date(2008, 7, 25),  11),
    ("Carol Singh",     "carol@school.edu",     date(2009, 11, 5),  10),
    ("David Lee",       "david@school.edu",     date(2007, 6, 18),  12),
    ("Eva Williams",    "eva@school.edu",       date(2010, 1, 30),   9),
    ("Farhan Ahmed",    "farhan@school.edu",    date(2008, 9, 14),  11),
    ("Gita Rao",        "gita@school.edu",      date(2009, 5, 22),  10),
    ("Hiro Tanaka",     "hiro@school.edu",      date(2007, 12, 8),  12),
    ("Isla Martin",     "isla@school.edu",      date(2010, 4, 3),    9),
    ("James Okafor",    "james@school.edu",     date(2008, 2, 19),  11),
]

# student_email → list of course titles to enrol in
ENROLLMENTS: dict[str, list[str]] = {
    "alice@school.edu":  ["Algebra II",         "Python Programming"],
    "bob@school.edu":    ["Calculus",            "Physics Mechanics"],
    "carol@school.edu":  ["Algebra II",          "Python Programming",  "Organic Chemistry"],
    "david@school.edu":  ["Calculus",            "Organic Chemistry",   "English Literature"],
    "eva@school.edu":    ["Algebra II",          "Python Programming"],
    "farhan@school.edu": ["Physics Mechanics",   "Python Programming"],
    "gita@school.edu":   ["Algebra II",          "Organic Chemistry"],
    "hiro@school.edu":   ["Calculus",            "Physics Mechanics",   "English Literature"],
    "isla@school.edu":   ["Algebra II",          "English Literature"],
    "james@school.edu":  ["Physics Mechanics",   "Calculus"],
}

EXAM_TYPES = [
    ("Quiz",       25,  16),
    ("Midterm",   100,  55),
    ("Assignment", 50,  32),
    ("Final",     100,  58),
]

SCHOOL_START = date(2026, 1, 5)
SCHOOL_DAYS  = 20


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────


def _get_or_create_teacher(svc: TeacherService, name, email, subject, phone):
    try:
        return svc.get_by_email(email)
    except SchoolError:
        return svc.hire(name, email, subject, phone)


def _get_or_create_student(svc: StudentService, name, email, dob, grade):
    try:
        return svc.get_by_email(email)
    except SchoolError:
        return svc.register(name, email, dob, grade)


def _get_or_create_course(svc: CourseService, title, teacher_id, max_st, credits):
    all_courses = svc.list_all()
    match = next((c for c in all_courses if c.title == title), None)
    if match:
        return match
    return svc.create(title, teacher_id, max_st, credits)


def _weekdays_from(start: date, count: int) -> list[date]:
    """Return `count` consecutive weekday dates starting from `start`."""
    days, d = [], start
    while len(days) < count:
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


# ─────────────────────────────────────────────────────────────────────────────
# MAIN SEEDER
# ─────────────────────────────────────────────────────────────────────────────


def seed(config: dict) -> None:
    random.seed(42)

    student_svc    = StudentService(config)
    teacher_svc    = TeacherService(config)
    course_svc     = CourseService(config)
    enrollment_svc = EnrollmentService(config)
    grade_svc      = GradeService(config)
    attendance_svc = AttendanceService(config)

    print("\n[SEED] Teachers...")
    teacher_map: dict[str, int] = {}   # email → id
    for name, email, subject, phone in TEACHERS:
        t = _get_or_create_teacher(teacher_svc, name, email, subject, phone)
        teacher_map[email] = t.id

    print("[SEED] Courses...")
    course_map: dict[str, int] = {}    # title → id
    for title, t_email, max_st, credits in COURSES:
        c = _get_or_create_course(course_svc, title,
                                  teacher_map[t_email], max_st, credits)
        course_map[title] = c.id

    print("[SEED] Students...")
    student_map: dict[str, int] = {}   # email → id
    for name, email, dob, grade in STUDENTS:
        s = _get_or_create_student(student_svc, name, email, dob, grade)
        student_map[email] = s.id

    print("[SEED] Enrollments...")
    # enrollment_map: (student_id, course_id) → enrollment_id
    enrollment_map: dict[tuple[int, int], int] = {}

    for s_email, course_titles in ENROLLMENTS.items():
        sid = student_map[s_email]
        for title in course_titles:
            cid = course_map[title]
            try:
                enr = enrollment_svc.enroll(sid, cid)
                enrollment_map[(sid, cid)] = enr.id
            except EnrollmentError:
                # Already enrolled — look up existing
                enr = enrollment_svc.get_enrollment(sid, cid)
                enrollment_map[(sid, cid)] = enr.id

    print("[SEED] Grades...")
    school_days = _weekdays_from(SCHOOL_START, SCHOOL_DAYS)
    for (sid, cid), enr_id in enrollment_map.items():
        existing = grade_svc.get_for_enrollment(enr_id)
        if existing:
            continue
        for exam_type, total, base_min in EXAM_TYPES:
            marks = round(random.uniform(base_min, total), 1)
            try:
                grade_svc.record(enr_id, exam_type, marks, float(total))
            except (SchoolError, ValueError) as exc:
                logger.warning("Grade skipped for enr=%d: %s", enr_id, exc)

    print("[SEED] Attendance...")
    statuses = (["Present"] * 8) + ["Late", "Absent"]
    for (sid, cid), enr_id in enrollment_map.items():
        existing = attendance_svc.get_for_enrollment(enr_id)
        if existing:
            continue
        random.seed(enr_id)
        for d in school_days:
            status = random.choice(statuses)
            try:
                attendance_svc.mark(enr_id, d, status)
            except (SchoolError, ValueError) as exc:
                logger.warning("Attendance skipped enr=%d %s: %s", enr_id, d, exc)

    print("\n[SEED] Done! Database populated with demo data.\n")
    print(f"  Teachers  : {len(TEACHERS)}")
    print(f"  Courses   : {len(COURSES)}")
    print(f"  Students  : {len(STUDENTS)}")
    print(f"  Enrollments: {len(enrollment_map)}")


# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    if not MYSQL_AVAILABLE:
        print("ERROR: mysql-connector-python not installed.")
        print("Run:   pip install mysql-connector-python")
        sys.exit(1)

    config = get_db_config()
    setup_database(config)
    seed(config)


if __name__ == "__main__":
    main()
