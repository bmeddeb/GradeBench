from django.db import models
from core.models import Team, Student
from core.async_utils import AsyncModelMixin


class Project(models.Model):  # Taiga Project
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="projects")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class Member(models.Model, AsyncModelMixin):  # Taiga Member
    """
    Taiga Member
    Links a Student to their membership in a Taiga project.
    """
    # One-to-one relationship ensures each Student has a single Taiga Member record
    student = models.OneToOneField(
        Student,
        on_delete=models.CASCADE,
        related_name="taiga_member",
        help_text="The Student associated with this Taiga member."
    )

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="members",
        help_text="The Taiga project this member belongs to."
    )
    role_name = models.CharField(
        max_length=100,
        help_text="Role of the member in the project (e.g., Developer, Manager)."
    )
    color = models.CharField(
        max_length=7,
        help_text="Hex color code associated with this role (e.g., '#ff0000')."
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this Member record was created."
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this Member record was last updated."
    )

    class Meta:
        unique_together = ("student", "project")
        verbose_name = "Taiga Member"
        verbose_name_plural = "Taiga Members"

    def __str__(self):
        return f"{self.student.full_name} as {self.role_name}"


class Sprint(models.Model):
    name = models.CharField(max_length=255)
    created_date = models.DateTimeField()
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    total_points = models.IntegerField(default=0)
    closed_points = models.IntegerField(default=0)
    project = models.ForeignKey(
        Project, on_delete=models.CASCADE, related_name="sprints"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class UserStory(models.Model):
    ref = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_date = models.DateTimeField()
    closed = models.BooleanField(default=False)
    total_points = models.IntegerField(default=0)
    modified_date = models.DateTimeField()
    in_sprint_date = models.DateTimeField()
    sprint = models.ForeignKey(
        Sprint, on_delete=models.CASCADE, related_name="user_stories"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.ref} - {self.name}"


class Task(models.Model):
    ref = models.CharField(max_length=50)
    name = models.TextField()
    created_date = models.DateTimeField()
    finished_date = models.DateTimeField(null=True, blank=True)
    is_closed = models.BooleanField(default=False)
    assigned_to = models.ForeignKey(
        Member, on_delete=models.SET_NULL, null=True, blank=True
    )
    user_story = models.ForeignKey(
        UserStory, on_delete=models.CASCADE, related_name="tasks"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class TaskEvent(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name="events")
    created_at = models.DateTimeField()
    status_before = models.CharField(max_length=100)
    status_after = models.CharField(max_length=100)
    in_progress_time = models.IntegerField()
    in_testing_time = models.IntegerField()
    recorded_at = models.DateTimeField(auto_now_add=True)


class TaskAssignmentEvent(models.Model):
    task = models.ForeignKey(
        Task, on_delete=models.CASCADE, related_name="assignment_events"
    )
    created_at = models.DateTimeField()
    assigned_to_before = models.IntegerField()
    assigned_to_after = models.IntegerField()
    recorded_at = models.DateTimeField(auto_now_add=True)
