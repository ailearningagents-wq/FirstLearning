"""
tests/test_models.py — Unit tests for pure dataclass models.
No database required.
"""

import pytest
from datetime import date

from school_management.models.student    import Student
from school_management.models.teacher    import Teacher
from school_management.models.course     import Course
from school_management.models.grade      import Grade
from school_management.models.attendance import Attendance


# ── Student ──────────────────────────────────────────────────────────────────

class TestStudent:
    def test_age_calculation(self):
        dob     = date(2010, 1, 1)
        student = Student(name="Test", email="t@t.com", dob=dob, grade_level=9)
        assert student.age() >= 14

    def test_invalid_grade_level(self):
        with pytest.raises(ValueError):
            Student(name="X", email="x@x.com", dob=date(2010, 1, 1), grade_level=13)

    def test_invalid_email(self):
        with pytest.raises(ValueError):
            Student(name="X", email="notanemail", dob=date(2010, 1, 1), grade_level=9)

    def test_str(self):
        s = Student(id=1, name="Alice", email="a@a.com",
                    dob=date(2010, 1, 1), grade_level=10)
        assert "Alice" in str(s)
        assert "10" in str(s)


# ── Teacher ───────────────────────────────────────────────────────────────────

class TestTeacher:
    def test_invalid_email(self):
        with pytest.raises(ValueError):
            Teacher(name="X", email="bad", subject_specialisation="Math", phone="000")

    def test_str(self):
        t = Teacher(id=2, name="Dr. Smith", email="s@s.com",
                    subject_specialisation="Physics", phone="1234567890")
        assert "Dr. Smith" in str(t)


# ── Course ────────────────────────────────────────────────────────────────────

class TestCourse:
    def test_invalid_max_students(self):
        with pytest.raises(ValueError):
            Course(title="X", teacher_id=1, max_students=0)

    def test_invalid_credits(self):
        with pytest.raises(ValueError):
            Course(title="X", teacher_id=1, credits=0)


# ── Grade ─────────────────────────────────────────────────────────────────────

class TestGrade:
    def test_percentage(self):
        g = Grade(enrollment_id=1, exam_type="Quiz", marks=18, total=25)
        assert g.percentage == 72.0

    def test_letter_grade_A_plus(self):
        g = Grade(enrollment_id=1, exam_type="Final", marks=95, total=100)
        assert g.letter_grade == "A+"

    def test_letter_grade_F(self):
        g = Grade(enrollment_id=1, exam_type="Final", marks=40, total=100)
        assert g.letter_grade == "F"

    def test_marks_cannot_exceed_total(self):
        with pytest.raises(ValueError):
            Grade(enrollment_id=1, exam_type="Quiz", marks=30, total=25)

    def test_negative_marks(self):
        with pytest.raises(ValueError):
            Grade(enrollment_id=1, exam_type="Quiz", marks=-1, total=25)

    def test_zero_total_raises(self):
        with pytest.raises(ValueError):
            Grade(enrollment_id=1, exam_type="Quiz", marks=0, total=0)


# ── Attendance ────────────────────────────────────────────────────────────────

class TestAttendance:
    def test_valid_status(self):
        a = Attendance(enrollment_id=1, date=date.today(), status="Present")
        assert a.status == "Present"

    def test_invalid_status(self):
        with pytest.raises(ValueError):
            Attendance(enrollment_id=1, date=date.today(), status="Holiday")
