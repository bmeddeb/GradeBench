# core/models.py
from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from core.async_utils import AsyncModelMixin
from core.mixins import TimestampedModel, SyncableModel
from encrypted_model_fields.fields import EncryptedCharField
from icalendar import Calendar, Event as ICalEvent
from datetime import datetime
import pytz


class UserProfile(TimestampedModel, AsyncModelMixin):
    """
    Base user profile with common fields for all users (instructors/professors/TAs)
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile")
    github_username = models.CharField(max_length=100, blank=True, null=True)
    github_access_token = EncryptedCharField(max_length=255, blank=True, null=True, help_text="Encrypted GitHub personal access token for API authentication")
    github_avatar_url = models.URLField(max_length=500, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    timezone = models.CharField(max_length=63, default="UTC")

    def __str__(self):
        return f"{self.user.username}'s profile"

    def is_professor(self):
        return hasattr(self, "professor_profile")

    def is_ta(self):
        return hasattr(self, "ta_profile")


class GitHubToken(TimestampedModel, AsyncModelMixin):
    """
    Model to store multiple GitHub tokens for professors and TAs
    """

    name = models.CharField(max_length=100)
    token = EncryptedCharField(help_text="Encrypted GitHub API token")
    scope = models.CharField(max_length=255, blank=True, null=True)
    last_used = models.DateTimeField(blank=True, null=True)
    rate_limit_remaining = models.IntegerField(default=5000)
    rate_limit_reset = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.scope}"

    def is_rate_limited(self):
        if self.rate_limit_remaining <= 10:
            if self.rate_limit_reset and self.rate_limit_reset > timezone.now():
                return True
        return False


class StaffProfile(TimestampedModel, AsyncModelMixin):
    """
    Base model for Professor and TA profiles with shared fields
    """

    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    github_tokens = models.ManyToManyField(GitHubToken, blank=True)
    lms_access_token = EncryptedCharField(
        max_length=255, blank=True, null=True, help_text="Encrypted Learning Management System (LMS) API access token")
    lms_refresh_token = EncryptedCharField(
        max_length=255, blank=True, null=True, help_text="Encrypted LMS API refresh token for obtaining new access tokens")
    lms_token_expires = models.DateTimeField(blank=True, null=True)

    class Meta:
        abstract = True


class ProfessorProfile(StaffProfile):
    department = models.CharField(max_length=100, blank=True, null=True)
    office_location = models.CharField(max_length=100, blank=True, null=True)
    office_hours = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Professor: {self.user_profile.user.get_full_name()}"


class TAProfile(StaffProfile):
    supervisor = models.ForeignKey(
        ProfessorProfile, on_delete=models.SET_NULL, blank=True, null=True
    )
    hours_per_week = models.PositiveIntegerField(default=20)
    expertise_areas = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"TA: {self.user_profile.user.get_full_name()}"


class TeamQuerySet(models.QuerySet):
    """
    Custom QuerySet for Team to provide common filtering methods
    and avoid repetitive .filter() calls.
    """
    def filter_by_canvas_course(self, course):
        """
        Return teams associated with a specific Canvas course.
        `course` can be a CanvasCourse instance or its primary key.
        """
        return self.filter(canvas_course=course)

    def filter_by_canvas_group(self, group_id):
        """
        Return teams with the specified Canvas group ID.
        """
        return self.filter(canvas_group_id=group_id)

    def filter_by_group_set(self, group_set_id):
        """
        Return teams belonging to the specified Canvas group set/category.
        """
        return self.filter(canvas_group_set_id=group_set_id)

    def filter_by_github_org(self, organization):
        """
        Return teams under a given GitHub organization.
        Case-insensitive match on github_organization.
        """
        return self.filter(github_organization__iexact=organization)

    def filter_by_taiga_project_name(self, project_name):
        """
        Return teams linked to a Taiga project by its name.
        Case-insensitive match on taiga_project.
        """
        return self.filter(taiga_project__iexact=project_name)


class TeamManager(models.Manager):
    """
    Custom Manager for Team that uses TeamQuerySet
    and exposes filtering methods directly on objects.
    """
    def get_queryset(self):
        return TeamQuerySet(self.model, using=self._db)

    def filter_by_canvas_course(self, course):
        return self.get_queryset().filter_by_canvas_course(course)

    def filter_by_canvas_group(self, group_id):
        return self.get_queryset().filter_by_canvas_group(group_id)

    def filter_by_group_set(self, group_set_id):
        return self.get_queryset().filter_by_group_set(group_set_id)

    def filter_by_github_org(self, organization):
        return self.get_queryset().filter_by_github_org(organization)

    def filter_by_taiga_project_name(self, project_name):
        return self.get_queryset().filter_by_taiga_project_name(project_name)


class Team(SyncableModel, AsyncModelMixin):
    """
    Student team model linking to GitHub, Taiga, and Canvas entities.
    """
    # Core fields
    name = models.CharField(
        max_length=100,
        help_text="Human-readable team name."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Optional detailed description of the team."
    )

    # GitHub integration
    github_organization = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="GitHub organization name for this team."
    )
    github_repo_name = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="GitHub repository name under the organization."
    )
    github_team_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="GitHub API team ID (numeric string)."
    )

    # Taiga integration
    taiga_project = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Taiga project slug or name."
    )
    taiga_project_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Taiga API project ID (numeric string)."
    )


    # Canvas integration fields
    canvas_course = models.ForeignKey(
        "lms.CanvasCourse",
        on_delete=models.CASCADE,
        related_name="teams",
        null=True,
        blank=True,
    )
    canvas_group_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Canvas group ID (from /api/v1/groups/:id)."
    )
    canvas_group_set_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Canvas group set (category) ID."
    )
    canvas_group_set_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Canvas group set (category) name."
    )

    # Sync metadata fields are inherited from SyncableModel

    # Attach the custom manager
    objects = TeamManager()

    class Meta:
        indexes = [
            models.Index(fields=["canvas_course", "canvas_group_id"]),
            models.Index(fields=["canvas_group_set_id"]),
        ]
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    def __str__(self):
        return self.name


class StudentQuerySet(models.QuerySet):
    """
    Custom QuerySet for Student to eagerly load related identity data
    and avoid N+1 queries.
    and now we can do:
    # Synchronous
    students = Student.objects.with_all_identities()

    # Async (Django 5.3+)
    students = await Student.objects.with_all_identities().aall()

    """

    def with_all_identities(self):
        """
        Eagerly load related fields to prevent N+1 queries when accessing
        team, creator, GitHub and Taiga profiles, and Canvas enrollments.
        """
        return (
            self
            .select_related(
                "team",  # Student.team
                "created_by",  # Student.created_by
                "github_collaborator",  # OneToOne GitHub profile
                "taiga_member"  # OneToOne Taiga profile
            )
            .prefetch_related(
                "canvas_enrollments"  # Student.canvas_enrollments
            )
        )

    def filter_by_team(self, team):
        """
        Filter students by their Team.

        `team` can be a Team instance or its primary key.
        """
        return self.filter(team=team)

    def filter_by_canvas_course(self, course):
        """
        Filter students enrolled in a given Canvas course.

        `course` can be a CanvasCourse instance or its primary key.
        Uses the reverse relationship on CanvasEnrollment.
        """
        return (
            self
            .filter(canvas_enrollments__course=course)
            .distinct()
        )

    def filter_by_github_username(self, username):
        """
        Filter students by GitHub username (case-insensitive).
        """
        return self.filter(github_collaborator__username__iexact=username)

    def filter_by_taiga_project(self, project):
        """
        Filter students who are members of a specific Taiga project.

        `project` can be a Project instance or its primary key.
        Uses the reverse relationship on Member.
        """
        return (
            self
            .filter(taiga_member__project=project)
            .distinct()
        )


class StudentManager(models.Manager):
    """
    Custom Manager for Student that uses StudentQuerySet
    and exposes identity-prefetching and filtering methods.
    """

    def get_queryset(self):
        return StudentQuerySet(self.model, using=self._db)

    def with_all_identities(self):
        return self.get_queryset().with_all_identities()

    def filter_by_team(self, team):
        return self.get_queryset().filter_by_team(team)

    def filter_by_canvas_course(self, course):
        return self.get_queryset().filter_by_canvas_course(course)

    def filter_by_github_username(self, username):
        return self.get_queryset().filter_by_github_username(username)

    def filter_by_taiga_project(self, project):
        return self.get_queryset().filter_by_taiga_project(project)


# Central Student model
class Student(TimestampedModel, AsyncModelMixin):
    """
    Central student entity that links identities across platforms.
    This is NOT tied to the Django user system - students don't log in.
    """

    # Basic student identification
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    student_id = models.CharField(
        max_length=20, blank=True, null=True, unique=True)

    # Team association
    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, blank=True, null=True, related_name="students"
    )
    
    # Avatar (supports both file upload and URL)
    avatar = models.ImageField(
        upload_to="student_avatars/", blank=True, null=True
    )
    avatar_url = models.URLField(max_length=500, blank=True, null=True)

    # Platform identifiers - these fields store the basic identifiers
    # that can be used to look up the full platform-specific profiles
    github_username = models.CharField(max_length=100, blank=True, null=True)
    taiga_username = models.CharField(max_length=100, blank=True, null=True)
    canvas_user_id = models.CharField(max_length=100, blank=True, null=True)

    # Metadata
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_students",
    )

    # Properties for convenience
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def get_avatar_url(self):
        """Get avatar URL, prioritizing uploaded image over URL field"""
        if self.avatar:
            return self.avatar.url
        return self.avatar_url

    @property
    def display_name(self):
        return self.full_name

    @property
    def github_profile(self):
        """Get associated GitHub collaborator profile if it exists"""
        from git_providers.github.models import Collaborator

        try:
            return Collaborator.objects.get(student=self)
        except Collaborator.DoesNotExist:
            return None

    @property
    def taiga_member(self):
        """Get associated Taiga member profile if it exists"""
        from project_mgmt.taiga.models import Member

        try:
            return Member.objects.get(student=self)
        except Member.DoesNotExist:
            return None

    @property
    def canvas_enrollments(self):
        """Get all Canvas enrollments for this student"""
        from lms.canvas.models import CanvasEnrollment

        return CanvasEnrollment.objects.filter(student=self)

    def __str__(self):
        if self.student_id:
            return f"{self.full_name} ({self.student_id})"
        return self.full_name

    @classmethod
    def fetch_with_identities(cls):
        """
        Returns students with all platform identities preloaded
        to avoid additional database queries when accessing them.
        """
        return cls.objects.with_all_identities()


class CalendarEvent(TimestampedModel, AsyncModelMixin):
    """
    Calendar event model that can be imported from iCalendar (.ics) files
    and displayed in a calendar view on the dashboard.
    """

    # Core fields
    uid = models.CharField(max_length=255, unique=True)  # Unique ID from .ics
    summary = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    # Time fields
    dtstart = models.DateTimeField()  # Start time
    dtend = models.DateTimeField(null=True, blank=True)  # End time (optional)
    all_day = models.BooleanField(default=False)  # True if no time component

    # Recurrence (if event repeats)
    # Stored as iCalendar RRULE string
    rrule = models.TextField(blank=True, null=True)

    # Metadata - inherits created_at and updated_at from TimestampedModel
    last_modified = models.DateTimeField(null=True, blank=True)  # From .ics

    # Calendar source
    source = models.CharField(
        max_length=100, blank=True, null=True
    )  # e.g., 'canvas', 'github', 'custom'

    # User association (optional) - if calendar is user-specific
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="calendar_events",
    )

    def __str__(self):
        return self.summary

    def to_dict(self):
        """Convert to dictionary for JSON serialization (for FullCalendar)"""
        event_dict = {
            "id": self.id,
            "title": self.summary,
            "start": self.dtstart.isoformat(),
            "allDay": self.all_day,
        }

        if self.dtend:
            event_dict["end"] = self.dtend.isoformat()

        if self.description:
            event_dict["description"] = self.description

        if self.location:
            event_dict["location"] = self.location

        return event_dict

    @classmethod
    def from_ics(cls, ics_file, source=None, user=None):
        """Parses an .ics file and creates/updates events in the database."""
        cal = Calendar.from_ical(ics_file.read())
        events_created = 0

        for component in cal.walk():
            if component.name == "VEVENT":
                uid = str(component.get("UID", ""))
                summary = str(component.get("SUMMARY", "Untitled Event"))
                description = str(component.get("DESCRIPTION", ""))
                location = str(component.get("LOCATION", ""))

                # Handle DTSTART (required)
                dtstart = component.get("DTSTART").dt
                if isinstance(dtstart, datetime) and dtstart.tzinfo is None:
                    dtstart = timezone.make_aware(
                        dtstart)  # Ensure timezone-aware
                elif not isinstance(dtstart, datetime):
                    # Convert date to datetime for all-day events
                    dtstart = timezone.make_aware(
                        datetime.combine(dtstart, datetime.min.time())
                    )

                # Handle DTEND (optional)
                dtend = component.get("DTEND")
                if dtend:
                    dtend = dtend.dt
                    if isinstance(dtend, datetime) and dtend.tzinfo is None:
                        dtend = timezone.make_aware(dtend)
                    elif not isinstance(dtend, datetime):
                        # Convert date to datetime for all-day events
                        dtend = timezone.make_aware(
                            datetime.combine(dtend, datetime.min.time())
                        )

                # Check if all-day event (DATE instead of DATETIME)
                all_day = not isinstance(component.get("DTSTART").dt, datetime)

                # Handle RRULE (recurrence)
                rrule = component.get("RRULE")
                if rrule:
                    rrule = rrule.to_ical().decode("utf-8")  # Convert to string

                # Get last modified if available
                last_modified = component.get("LAST-MODIFIED")
                if last_modified:
                    last_modified = last_modified.dt
                    if last_modified.tzinfo is None:
                        last_modified = timezone.make_aware(last_modified)

                # Create or update event
                event, created = cls.objects.update_or_create(
                    uid=uid,
                    defaults={
                        "summary": summary,
                        "description": description,
                        "location": location,
                        "dtstart": dtstart,
                        "dtend": dtend,
                        "all_day": all_day,
                        "rrule": rrule,
                        "last_modified": last_modified,
                        "source": source,
                        "user": user,
                    },
                )

                if created:
                    events_created += 1

        return events_created


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    from django.db import connection

    # Check if the UserProfile table exists
    with connection.cursor() as cursor:
        table_name = UserProfile._meta.db_table
        try:
            cursor.execute(
                f"SELECT 1 FROM sqlite_master WHERE type='table' AND name='{table_name}';"
            )
            table_exists = cursor.fetchone() is not None
        except:
            table_exists = False

    if created and table_exists:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    # Check if the profile field exists before saving
    if hasattr(instance, "profile"):
        instance.profile.save()


# Define functions to assign users to groups and create appropriate profiles
def set_as_professor(user, department=None, office_location=None, office_hours=None):
    """Set a user as a professor"""
    # Add to professor group
    professor_group, _ = Group.objects.get_or_create(name="Professors")
    user.groups.add(professor_group)

    # Create professor profile if it doesn't exist
    if not hasattr(user.profile, "professor_profile"):
        professor_profile = ProfessorProfile.objects.create(
            user_profile=user.profile,
            department=department,
            office_location=office_location,
            office_hours=office_hours,
        )
        return professor_profile
    return user.profile.professor_profile


def set_as_ta(user, supervisor=None, hours_per_week=20, expertise_areas=None):
    """Set a user as a TA"""
    # Add to TA group
    ta_group, _ = Group.objects.get_or_create(name="TAs")
    user.groups.add(ta_group)

    # Create TA profile if it doesn't exist
    if not hasattr(user.profile, "ta_profile"):
        ta_profile = TAProfile.objects.create(
            user_profile=user.profile,
            supervisor=supervisor,
            hours_per_week=hours_per_week,
            expertise_areas=expertise_areas,
        )
        return ta_profile
    return user.profile.ta_profile
