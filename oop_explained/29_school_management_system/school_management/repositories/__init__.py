"""repositories/__init__.py"""

from .student_repo    import StudentRepository
from .teacher_repo    import TeacherRepository
from .course_repo     import CourseRepository
from .enrollment_repo import EnrollmentRepository
from .grade_repo      import GradeRepository
from .attendance_repo import AttendanceRepository

__all__ = [
    "StudentRepository",
    "TeacherRepository",
    "CourseRepository",
    "EnrollmentRepository",
    "GradeRepository",
    "AttendanceRepository",
]
