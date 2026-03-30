"""
tests/test_services.py — Unit tests for the service layer.

All database calls are mocked via pytest-mock, so no real MySQL
connection is needed to run these tests.
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

from school_management.models     import Student, Teacher, Course, Enrollment, Grade
from school_management.exceptions import (
    StudentNotFound, EnrollmentError, GradeError, TeacherNotFound
)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def _make_student(id_=1) -> Student:
    return Student(id=id_, name="Alice", email=f"alice{id_}@s.com",
                   dob=date(2009, 3, 12), grade_level=10)

def _make_teacher(id_=1) -> Teacher:
    return Teacher(id=id_, name="Dr. Smith", email="smith@s.com",
                   subject_specialisation="Math", phone="0000000000")

def _make_course(id_=1, max_students=30) -> Course:
    return Course(id=id_, title="Algebra", teacher_id=1,
                  max_students=max_students, credits=4)

def _make_enrollment(id_=1, sid=1, cid=1) -> Enrollment:
    return Enrollment(id=id_, student_id=sid, course_id=cid,
                      enrolled_on=date.today())


# ─────────────────────────────────────────────────────────────────────────────
# StudentService
# ─────────────────────────────────────────────────────────────────────────────

class TestStudentService:

    def test_register_returns_student(self, mocker):
        from school_management.services.student_service import StudentService
        mock_repo = MagicMock()
        expected  = _make_student()
        mock_repo.add.return_value = expected
        mocker.patch(
            "school_management.services.student_service.StudentRepository",
            return_value=mock_repo,
        )
        svc    = StudentService({})
        result = svc.register("Alice", "alice@s.com", date(2009,3,12), 10)
        assert result == expected
        mock_repo.add.assert_called_once()

    def test_get_raises_when_not_found(self, mocker):
        from school_management.services.student_service import StudentService
        mock_repo = MagicMock()
        mock_repo.get_by_id.side_effect = StudentNotFound("nope")
        mocker.patch(
            "school_management.services.student_service.StudentRepository",
            return_value=mock_repo,
        )
        svc = StudentService({})
        with pytest.raises(StudentNotFound):
            svc.get(999)

    def test_total_count(self, mocker):
        from school_management.services.student_service import StudentService
        mock_repo = MagicMock()
        mock_repo.count.return_value = 7
        mocker.patch(
            "school_management.services.student_service.StudentRepository",
            return_value=mock_repo,
        )
        assert StudentService({}).total_count() == 7


# ─────────────────────────────────────────────────────────────────────────────
# EnrollmentService
# ─────────────────────────────────────────────────────────────────────────────

class TestEnrollmentService:

    def _mock_enr_service(self, mocker, *, student=None, course=None,
                          enrolled_count=0, add_side_effect=None):
        from school_management.services.enrollment_service import EnrollmentService

        mock_s_repo = MagicMock()
        mock_c_repo = MagicMock()
        mock_e_repo = MagicMock()

        mock_s_repo.get_by_id.return_value = student or _make_student()
        mock_c_repo.get_by_id.return_value  = course  or _make_course()
        mock_c_repo.enrolled_count.return_value = enrolled_count

        if add_side_effect:
            mock_e_repo.add.side_effect = add_side_effect
        else:
            mock_e_repo.add.return_value = _make_enrollment()

        mocker.patch("school_management.services.enrollment_service.StudentRepository",
                     return_value=mock_s_repo)
        mocker.patch("school_management.services.enrollment_service.CourseRepository",
                     return_value=mock_c_repo)
        mocker.patch("school_management.services.enrollment_service.EnrollmentRepository",
                     return_value=mock_e_repo)

        return EnrollmentService({})

    def test_enroll_success(self, mocker):
        svc = self._mock_enr_service(mocker)
        enr = svc.enroll(1, 1)
        assert enr is not None

    def test_enroll_raises_when_course_full(self, mocker):
        svc = self._mock_enr_service(
            mocker, course=_make_course(max_students=2), enrolled_count=2
        )
        with pytest.raises(EnrollmentError, match="full capacity"):
            svc.enroll(1, 1)

    def test_enroll_raises_on_duplicate(self, mocker):
        svc = self._mock_enr_service(
            mocker,
            add_side_effect=EnrollmentError("already enrolled"),
        )
        with pytest.raises(EnrollmentError):
            svc.enroll(1, 1)


# ─────────────────────────────────────────────────────────────────────────────
# GradeService
# ─────────────────────────────────────────────────────────────────────────────

class TestGradeService:

    def _patch_grade_service(self, mocker, *, avg=75.0, grades=None):
        from school_management.services.grade_service import GradeService

        mock_g_repo  = MagicMock()
        mock_e_repo  = MagicMock()

        mock_e_repo.get_by_id.return_value    = _make_enrollment()
        mock_g_repo.weighted_average.return_value = avg
        mock_g_repo.get_by_enrollment.return_value = grades or []
        mock_g_repo.add.side_effect = lambda g: g   # return same grade

        mocker.patch("school_management.services.grade_service.GradeRepository",
                     return_value=mock_g_repo)
        mocker.patch("school_management.services.grade_service.EnrollmentRepository",
                     return_value=mock_e_repo)
        return GradeService({})

    def test_record_valid_grade(self, mocker):
        svc = self._patch_grade_service(mocker)
        g   = svc.record(1, "Quiz", 18.0, 25.0)
        assert g.marks   == 18.0
        assert g.total   == 25.0

    def test_average_delegates_to_repo(self, mocker):
        svc = self._patch_grade_service(mocker, avg=82.5)
        assert svc.average(1) == 82.5

    def test_record_rejects_invalid_marks(self, mocker):
        svc = self._patch_grade_service(mocker)
        with pytest.raises(ValueError):
            svc.record(1, "Quiz", 30.0, 25.0)   # marks > total → Grade.__post_init__ raises
