from django.db import models
from core.async_utils import AsyncModelMixin


class LMSProvider(models.Model, AsyncModelMixin):
    """
    Abstract base model for all Learning Management System providers.

    This defines the common interface that all LMS providers must implement.
    """

    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True

    async def authenticate(self, **kwargs):
        """
        Authenticate with the LMS provider.

        Args:
            **kwargs: Provider-specific authentication parameters

        Returns:
            bool: True if authentication was successful
        """
        raise NotImplementedError("Subclasses must implement authenticate()")

    async def get_courses(self, **kwargs):
        """
        Fetch courses from the LMS provider.

        Args:
            **kwargs: Provider-specific parameters

        Returns:
            list: List of course information
        """
        raise NotImplementedError("Subclasses must implement get_courses()")

    async def get_assignments(self, course, **kwargs):
        """
        Fetch assignments for a specific course.

        Args:
            course: Course identifier
            **kwargs: Provider-specific parameters

        Returns:
            list: List of assignment information
        """
        raise NotImplementedError("Subclasses must implement get_assignments()")

    async def get_students(self, course, **kwargs):
        """
        Fetch students enrolled in a specific course.

        Args:
            course: Course identifier
            **kwargs: Provider-specific parameters

        Returns:
            list: List of student information
        """
        raise NotImplementedError("Subclasses must implement get_students()")

    async def submit_grade(self, assignment, student, grade, **kwargs):
        """
        Submit a grade for a student's assignment.

        Args:
            assignment: Assignment identifier
            student: Student identifier
            grade: Grade value
            **kwargs: Provider-specific parameters

        Returns:
            bool: True if submission was successful
        """
        raise NotImplementedError("Subclasses must implement submit_grade()")
