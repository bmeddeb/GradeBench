# File: lms/canvas/client.py
"""
Async client for interacting with the Canvas API.
"""
import logging
from django.utils import timezone

# Import mixins
from lms.canvas.mixins.request_mixin import RequestMixin
from lms.canvas.mixins.course_mixin import CourseMixin
from lms.canvas.mixins.enrollment_mixin import EnrollmentMixin
from lms.canvas.mixins.assignment_mixin import AssignmentMixin
from lms.canvas.mixins.group_mixin import GroupMixin
from lms.canvas.mixins.sync_mixin import SyncMixin
from lms.canvas.mixins.quiz_mixin import QuizMixin

# Import models
from .models import (
    CanvasAssignment,
    CanvasCourse,
    CanvasEnrollment,
    CanvasIntegration,
    CanvasRubric,
    CanvasRubricCriterion,
    CanvasRubricRating,
    CanvasSubmission,
    CanvasGroupCategory,
    CanvasGroup,
    CanvasGroupMembership,
    CanvasQuiz,
)
from core.models import Student

logger = logging.getLogger(__name__)


class Client(RequestMixin, CourseMixin, EnrollmentMixin, AssignmentMixin, GroupMixin, SyncMixin, QuizMixin):
    """Async client for interacting with the Canvas API"""

    def __init__(self, integration: CanvasIntegration):
        """Initialize with a CanvasIntegration instance"""
        self.integration = integration
        self.base_url = integration.canvas_url
        self.api_key = integration.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        # Make frequently used dependencies available to mixins
        self.timezone = timezone

        # Create a namespace with all models to make them available to mixins
        self.models = type('Models', (), {
            'CanvasCourse': CanvasCourse,
            'CanvasAssignment': CanvasAssignment,
            'CanvasEnrollment': CanvasEnrollment,
            'CanvasSubmission': CanvasSubmission,
            'CanvasRubric': CanvasRubric,
            'CanvasRubricCriterion': CanvasRubricCriterion,
            'CanvasRubricRating': CanvasRubricRating,
            'CanvasGroupCategory': CanvasGroupCategory,
            'CanvasGroup': CanvasGroup,
            'CanvasGroupMembership': CanvasGroupMembership,
            'CanvasQuiz': CanvasQuiz,
            'Student': Student,
        })
