from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from core.async_utils import AsyncModelMixin


class UserProfile(models.Model, AsyncModelMixin):
    """
    Base user profile with common fields for all users (instructors/professors/TAs)
    """
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='profile'
    )
    github_username = models.CharField(max_length=100, blank=True, null=True)
    github_access_token = models.CharField(
        max_length=255, blank=True, null=True
    )
    github_avatar_url = models.URLField(
        max_length=500, blank=True, null=True
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', blank=True, null=True
    )
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s profile"

    def is_professor(self):
        return hasattr(self, 'professor_profile')

    def is_ta(self):
        return hasattr(self, 'ta_profile')
        
    def is_student(self):
        return hasattr(self, 'student_profile')


class GitHubToken(models.Model, AsyncModelMixin):
    """
    Model to store multiple GitHub tokens for professors and TAs
    """
    name = models.CharField(max_length=100)
    token = models.CharField(max_length=255)
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
    user_profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE
    )
    github_tokens = models.ManyToManyField(GitHubToken, blank=True)
    lms_access_token = models.CharField(max_length=255, blank=True, null=True)
    lms_refresh_token = models.CharField(max_length=255, blank=True, null=True)
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
        ProfessorProfile, on_delete=models.SET_NULL,
        blank=True, null=True
    )
    hours_per_week = models.PositiveIntegerField(default=20)
    expertise_areas = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"TA: {self.user_profile.user.get_full_name()}"


class Team(models.Model, AsyncModelMixin):
    "Student team model"
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    github_organization = models.CharField(
        max_length=100, blank=True, null=True
    )
    github_team_id = models.CharField(max_length=100, blank=True, null=True)
    taiga_project_id = models.CharField(
        max_length=100, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


# New decoupled Student model
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
        Team, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='students'
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
        User, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='created_students'
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
            'github': self.github_profile,
            'taiga': self.taiga_member,
            'canvas_enrollments': list(self.canvas_enrollments),
        }

    async def async_get_platform_identities(self):
        """Async version of get_platform_identities"""
        from asgiref.sync import sync_to_async

        # Get identities with async calls
        github_profile = await sync_to_async(lambda: self.github_profile)()
        taiga_member = await sync_to_async(lambda: self.taiga_member)()
        canvas_enrollments = await sync_to_async(list)(self.canvas_enrollments)

        return {
            'github': github_profile,
            'taiga': taiga_member,
            'canvas_enrollments': canvas_enrollments,
        }


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


# Define functions to assign users to groups and create appropriate profiles
def set_as_professor(user, department=None, office_location=None, office_hours=None):
    """Set a user as a professor"""
    # Add to professor group
    professor_group, _ = Group.objects.get_or_create(name='Professors')
    user.groups.add(professor_group)

    # Create professor profile if it doesn't exist
    if not hasattr(user.profile, 'professor_profile'):
        professor_profile = ProfessorProfile.objects.create(
            user_profile=user.profile,
            department=department,
            office_location=office_location,
            office_hours=office_hours
        )
        return professor_profile
    return user.profile.professor_profile


def set_as_ta(user, supervisor=None, hours_per_week=20, expertise_areas=None):
    """Set a user as a TA"""
    # Add to TA group
    ta_group, _ = Group.objects.get_or_create(name='TAs')
    user.groups.add(ta_group)

    # Create TA profile if it doesn't exist
    if not hasattr(user.profile, 'ta_profile'):
        ta_profile = TAProfile.objects.create(
            user_profile=user.profile,
            supervisor=supervisor,
            hours_per_week=hours_per_week,
            expertise_areas=expertise_areas
        )
        return ta_profile
    return user.profile.ta_profile


class StudentProfile(models.Model, AsyncModelMixin):
    """
    Legacy student profile model - maintained temporarily for backward compatibility.
    Will be phased out in favor of the new Student model.
    """
    user_profile = models.OneToOneField(
        UserProfile, on_delete=models.CASCADE,
        related_name='student_profile'
    )
    student_id = models.CharField(max_length=20, blank=True, null=True)
    team = models.ForeignKey(
        Team, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='members'
    )
    github_username = models.CharField(max_length=100, blank=True, null=True)
    taiga_username = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Student: {self.user_profile.user.get_full_name()}"


def set_as_student(user, student_id=None, team=None, github_username=None, taiga_username=None):
    """Set a user as a student (legacy method)"""
    # Add to student group
    student_group, _ = Group.objects.get_or_create(name='Students')
    user.groups.add(student_group)

    # Create student profile if it doesn't exist
    if not hasattr(user.profile, 'student_profile'):
        # Update github_username in the main profile if provided
        if github_username and not user.profile.github_username:
            user.profile.github_username = github_username
            user.profile.save()

        student_profile = StudentProfile.objects.create(
            user_profile=user.profile,
            student_id=student_id,
            team=team,
            github_username=github_username,
            taiga_username=taiga_username
        )
        return student_profile
    return user.profile.student_profile
