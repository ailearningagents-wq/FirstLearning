"""exceptions.py — Domain-specific exception hierarchy."""


class SchoolError(Exception):
    """Base exception for all School Management errors."""


class StudentNotFound(SchoolError):
    """Raised when a student record does not exist."""


class TeacherNotFound(SchoolError):
    """Raised when a teacher record does not exist."""


class CourseNotFound(SchoolError):
    """Raised when a course record does not exist."""


class EnrollmentNotFound(SchoolError):
    """Raised when an enrollment record does not exist."""


class EnrollmentError(SchoolError):
    """Raised when enrollment business-rules are violated."""


class GradeError(SchoolError):
    """Raised when a grade value is invalid."""


class AttendanceError(SchoolError):
    """Raised when an attendance value is invalid."""


class DatabaseError(SchoolError):
    """Wraps unexpected low-level database errors."""
