from django.db import models
from django.contrib.auth.models import User
from encrypted_model_fields.fields import EncryptedCharField
from core.async_utils import AsyncModelMixin
from core.mixins import TimestampedModel, SyncableModel
from django.utils import timezone
from .querysets import (
    CanvasCourseManager,
    CanvasEnrollmentManager,
    CanvasAssignmentManager,
    CanvasSubmissionManager,
    CanvasGroupCategoryManager,
    CanvasGroupManager,
    CanvasQuizManager,
)


class CanvasIntegration(SyncableModel):
    """Configuration for Canvas API integration"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="canvas_integrations"
    )
    canvas_url = models.URLField(default="https://canvas.instructure.com")
    api_key = EncryptedCharField(max_length=255, help_text="Encrypted Canvas API key for authentication")  # Encrypts the key
    refresh_token = EncryptedCharField(
        max_length=255, blank=True, null=True,
        help_text="Encrypted Canvas OAuth2 refresh token"
    )  # Also encrypt refresh token

    def __str__(self):
        return f"Canvas integration for {self.user.username}"


class CanvasCourse(TimestampedModel, AsyncModelMixin):
    """Canvas Course Information"""

    integration = models.ForeignKey(
        CanvasIntegration,
        on_delete=models.CASCADE,
        related_name="courses",
        null=True,
        blank=True,
    )
    canvas_id = models.PositiveIntegerField(unique=True, default=0)
    name = models.CharField(max_length=255)
    course_code = models.CharField(max_length=255)
    start_at = models.DateTimeField(null=True, blank=True)
    end_at = models.DateTimeField(null=True, blank=True)
    is_public = models.BooleanField(default=False)
    syllabus_body = models.TextField(blank=True, null=True)
    workflow_state = models.CharField(max_length=50, default="unpublished")
    time_zone = models.CharField(max_length=100, blank=True, null=True)
    uuid = models.CharField(max_length=255, blank=True, null=True)

    objects = CanvasCourseManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.course_code}: {self.name}"


class CanvasEnrollment(TimestampedModel, AsyncModelMixin):
    """Canvas Enrollment (Student or Teacher in a Course)"""

    ENROLLMENT_TYPES = (
        ("StudentEnrollment", "Student"),
        ("TeacherEnrollment", "Teacher"),
        ("TaEnrollment", "Teaching Assistant"),
        ("DesignerEnrollment", "Designer"),
        ("ObserverEnrollment", "Observer"),
        ("StudentViewEnrollment", "Test Student"),
    )

    ENROLLMENT_STATES = (
        ("active", "Active"),
        ("invited", "Invited"),
        ("rejected", "Rejected"),
        ("completed", "Completed"),
        ("inactive", "Inactive"),
    )

    objects = CanvasEnrollmentManager()

    canvas_id = models.PositiveIntegerField(unique=True, default=0)
    course = models.ForeignKey(
        CanvasCourse, on_delete=models.CASCADE, related_name="enrollments"
    )
    user_id = models.PositiveIntegerField()
    user_name = models.CharField(max_length=255)
    sortable_name = models.CharField(max_length=255, blank=True, null=True)
    short_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    role = models.CharField(
        max_length=50, choices=ENROLLMENT_TYPES, default="StudentEnrollment"
    )
    enrollment_state = models.CharField(
        max_length=20, choices=ENROLLMENT_STATES, default="active"
    )
    last_activity_at = models.DateTimeField(null=True, blank=True)
    grades = models.JSONField(default=dict, blank=True)
    # Link to student in the core app
    student = models.ForeignKey(
        "core.Student",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="canvas_enrollments",
    )

    class Meta:
        ordering = ["sortable_name"]
        unique_together = ("course", "user_id")

    def __str__(self):
        return f"{self.user_name} in {self.course}"


class CanvasAssignment(TimestampedModel, AsyncModelMixin):
    """Canvas Assignment Information"""

    objects = CanvasAssignmentManager()

    GRADING_TYPES = (
        ("points", "Points"),
        ("percent", "Percentage"),
        ("letter_grade", "Letter Grade"),
        ("gpa_scale", "GPA Scale"),
        ("pass_fail", "Pass/Fail"),
        ("not_graded", "Not Graded"),
    )

    canvas_id = models.PositiveIntegerField(unique=True)
    course = models.ForeignKey(
        CanvasCourse, on_delete=models.CASCADE, related_name="assignments"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    points_possible = models.FloatField(default=0.0)
    due_at = models.DateTimeField(null=True, blank=True)
    unlock_at = models.DateTimeField(null=True, blank=True)
    lock_at = models.DateTimeField(null=True, blank=True)
    position = models.IntegerField(default=0)
    grading_type = models.CharField(
        max_length=20, choices=GRADING_TYPES, default="points"
    )
    published = models.BooleanField(default=False)
    submission_types = models.JSONField(default=list, blank=True)
    has_submitted_submissions = models.BooleanField(default=False)
    muted = models.BooleanField(default=False)
    html_url = models.URLField(blank=True, null=True)
    has_overrides = models.BooleanField(default=False)
    needs_grading_count = models.IntegerField(default=0)
    is_quiz_assignment = models.BooleanField(default=False)

    class Meta:
        ordering = ["position"]

    def __str__(self):
        return f"{self.name} ({self.course})"


class CanvasSubmission(TimestampedModel, AsyncModelMixin):
    """Canvas Assignment Submission"""

    objects = CanvasSubmissionManager()

    SUBMISSION_STATES = (
        ("submitted", "Submitted"),
        ("graded", "Graded"),
        ("pending_review", "Pending Review"),
        ("unsubmitted", "Unsubmitted"),
    )

    canvas_id = models.PositiveIntegerField(unique=True)
    assignment = models.ForeignKey(
        CanvasAssignment, on_delete=models.CASCADE, related_name="submissions"
    )
    enrollment = models.ForeignKey(
        CanvasEnrollment, on_delete=models.CASCADE, related_name="submissions"
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    grade = models.CharField(max_length=50, blank=True, null=True)
    score = models.FloatField(null=True, blank=True)
    workflow_state = models.CharField(
        max_length=20, choices=SUBMISSION_STATES, default="unsubmitted"
    )
    late = models.BooleanField(default=False)
    excused = models.BooleanField(default=False)
    missing = models.BooleanField(default=False)
    submission_type = models.CharField(max_length=50, blank=True, null=True)
    url = models.URLField(blank=True, null=True)
    body = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-submitted_at"]
        unique_together = ("assignment", "enrollment")

    def __str__(self):
        return f"Submission by {self.enrollment.user_name} for {self.assignment.name}"


class CanvasRubric(TimestampedModel, AsyncModelMixin):
    """Canvas Rubric for Assessment"""

    canvas_id = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)
    points_possible = models.FloatField(default=0.0)

    def __str__(self):
        return self.title


class CanvasRubricCriterion(models.Model, AsyncModelMixin):
    """Individual criteria within a rubric"""

    rubric = models.ForeignKey(
        CanvasRubric, on_delete=models.CASCADE, related_name="criteria"
    )
    canvas_id = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    long_description = models.TextField(blank=True, null=True)
    points = models.FloatField(default=0.0)
    criterion_use_range = models.BooleanField(default=False)

    class Meta:
        unique_together = ("rubric", "canvas_id")

    def __str__(self):
        return f"{self.description} ({self.points} pts)"


class CanvasRubricRating(models.Model, AsyncModelMixin):
    """Rating levels for a rubric criterion"""

    criterion = models.ForeignKey(
        CanvasRubricCriterion, on_delete=models.CASCADE, related_name="ratings"
    )
    canvas_id = models.CharField(max_length=255)
    description = models.CharField(max_length=255)
    long_description = models.TextField(blank=True, null=True)
    points = models.FloatField(default=0.0)

    class Meta:
        unique_together = ("criterion", "canvas_id")

    def __str__(self):
        return f"{self.description} ({self.points} pts)"


class CanvasGroupCategory(SyncableModel, AsyncModelMixin):
    """Represents a Canvas Group Category/Group Set"""

    objects = CanvasGroupCategoryManager()

    canvas_id = models.PositiveIntegerField(unique=True)
    course = models.ForeignKey(
        CanvasCourse, on_delete=models.CASCADE, related_name="group_categories"
    )
    name = models.CharField(max_length=255)
    self_signup = models.CharField(max_length=50, null=True, blank=True)
    auto_leader = models.CharField(max_length=50, null=True, blank=True)
    group_limit = models.IntegerField(null=True, blank=True)
    canvas_created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name_plural = "Canvas Group Categories"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} (Course: {self.course.name})"


class CanvasGroup(SyncableModel, AsyncModelMixin):
    """Represents a Canvas Group within a Group Category"""

    objects = CanvasGroupManager()

    canvas_id = models.PositiveIntegerField(unique=True)
    category = models.ForeignKey(
        CanvasGroupCategory, on_delete=models.CASCADE, related_name="groups"
    )
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    canvas_created_at = models.DateTimeField(null=True, blank=True)

    # Optional link to a Team in the core app
    core_team = models.OneToOneField(
        "core.Team",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="canvas_group_link",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} (Category: {self.category.name})"


class CanvasGroupMembership(TimestampedModel, AsyncModelMixin):
    """Represents a student's membership in a Canvas Group"""

    group = models.ForeignKey(
        CanvasGroup, on_delete=models.CASCADE, related_name="memberships"
    )
    user_id = models.PositiveIntegerField()  # Canvas user ID
    student = models.ForeignKey(
        "core.Student",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="canvas_group_memberships",
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)

    class Meta:
        unique_together = ("group", "user_id")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} in {self.group.name}"


class CanvasQuiz(TimestampedModel, AsyncModelMixin):
    """Canvas Quiz Information"""

    objects = CanvasQuizManager()

    QUIZ_TYPES = (
        ("assignment", "Assignment"),
        ("practice_quiz", "Practice Quiz"),
        ("graded_survey", "Graded Survey"),
        ("survey", "Survey"),
    )

    canvas_id = models.PositiveIntegerField(unique=True)
    course = models.ForeignKey(
        CanvasCourse, on_delete=models.CASCADE, related_name="quizzes"
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    quiz_type = models.CharField(
        max_length=20, choices=QUIZ_TYPES, default="assignment"
    )
    assignment = models.OneToOneField(
        CanvasAssignment,
        on_delete=models.CASCADE,
        related_name="quiz",
        null=True,
        blank=True
    )
    time_limit = models.PositiveIntegerField(
        null=True, blank=True)  # in minutes
    shuffle_answers = models.BooleanField(default=False)
    one_question_at_a_time = models.BooleanField(default=False)
    show_correct_answers = models.BooleanField(default=True)
    hide_results = models.CharField(max_length=50, null=True, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    lock_at = models.DateTimeField(null=True, blank=True)
    unlock_at = models.DateTimeField(null=True, blank=True)
    points_possible = models.FloatField(default=0.0)
    scoring_policy = models.CharField(max_length=50, null=True, blank=True)
    published = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Canvas Quizzes"

    def __str__(self):
        return f"{self.title} ({self.course})"
