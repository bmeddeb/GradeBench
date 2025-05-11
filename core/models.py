# core/models.py
from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from core.async_utils import AsyncModelMixin
from encrypted_model_fields.fields import EncryptedCharField
from icalendar import Calendar, Event as ICalEvent
from datetime import datetime
import pytz


class UserProfile(models.Model, AsyncModelMixin):
    """
    Base user profile with common fields for all users (instructors/professors/TAs)
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    github_username = models.CharField(max_length=100, blank=True, null=True)
    github_access_token = EncryptedCharField(max_length=255, blank=True, null=True)
    github_avatar_url = models.URLField(max_length=500, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def is_professor(self):
        return hasattr(self, "professor_profile")

    def is_ta(self):
        return hasattr(self, "ta_profile")


class GitHubToken(models.Model, AsyncModelMixin):
    """
    Model to store multiple GitHub tokens for professors and TAs
    """

    name = models.CharField(max_length=100)
    token = EncryptedCharField()
    scope = models.CharField(max_length=255, blank=True, null=True)
    last_used = models.DateTimeField(blank=True, null=True)
    rate_limit_remaining = models.IntegerField(default=5000)
    rate_limit_reset = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.scope}"

    def is_rate_limited(self):
        if self.rate_limit_remaining <= 10:
            if self.rate_limit_reset and self.rate_limit_reset > timezone.now():
                return True
        return False


class StaffProfile(models.Model, AsyncModelMixin):
    """
    Base model for Professor and TA profiles with shared fields
    """

    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE)
    github_tokens = models.ManyToManyField(GitHubToken, blank=True)
    lms_access_token = EncryptedCharField(max_length=255, blank=True, null=True)
    lms_refresh_token = EncryptedCharField(max_length=255, blank=True, null=True)
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


class Team(models.Model, AsyncModelMixin):
    """Student team model"""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    github_organization = models.CharField(max_length=100, blank=True, null=True)
    github_team_id = models.CharField(max_length=100, blank=True, null=True)
    taiga_project_id = models.CharField(max_length=100, blank=True, null=True)
    # Canvas integration fields
    canvas_course = models.ForeignKey(
        "lms.CanvasCourse",
        on_delete=models.CASCADE,
        related_name="teams",
        null=True,
        blank=True,
    )
    canvas_group_id = models.PositiveIntegerField(
        null=True, blank=True, db_index=True, help_text="Canvas /api/v1/groups/:id"
    )
    last_synced_at = models.DateTimeField(
        null=True, blank=True, help_text="When this team was last synced with Canvas"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["canvas_course", "canvas_group_id"])]

    def __str__(self):
        return self.name


# Central Student model
class Student(models.Model, AsyncModelMixin):
    """
    Central student entity that links identities across platforms.
    This is NOT tied to the Django user system - students don't log in.
    """

    # Basic student identification
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    student_id = models.CharField(max_length=20, blank=True, null=True, unique=True)

    # Team association
    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL, blank=True, null=True, related_name="students"
    )

    # Platform identifiers - these fields store the basic identifiers
    # that can be used to look up the full platform-specific profiles
    github_username = models.CharField(max_length=100, blank=True, null=True)
    taiga_username = models.CharField(max_length=100, blank=True, null=True)
    canvas_user_id = models.CharField(max_length=100, blank=True, null=True)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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

    def get_platform_identities(self):
        """Get a dictionary of all platform identities for this student"""
        return {
            "github": self.github_profile,
            "taiga": self.taiga_member,
            "canvas_enrollments": list(self.canvas_enrollments),
        }

    async def async_get_platform_identities(self):
        """Async version of get_platform_identities"""
        from asgiref.sync import sync_to_async

        # Get identities with async calls
        github_profile = await sync_to_async(lambda: self.github_profile)()
        taiga_member = await sync_to_async(lambda: self.taiga_member)()
        canvas_enrollments = await sync_to_async(list)(self.canvas_enrollments)

        return {
            "github": github_profile,
            "taiga": taiga_member,
            "canvas_enrollments": canvas_enrollments,
        }


class CalendarEvent(models.Model, AsyncModelMixin):
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
    rrule = models.TextField(blank=True, null=True)  # Stored as iCalendar RRULE string

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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
                    dtstart = timezone.make_aware(dtstart)  # Ensure timezone-aware
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
