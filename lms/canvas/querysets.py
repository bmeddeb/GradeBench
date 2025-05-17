"""
Canvas model QuerySets and Managers for efficient database queries.
Supports both sync and async operations.
"""
from django.db import models
from django.utils import timezone
from datetime import timedelta
from asgiref.sync import sync_to_async


# CanvasCourse QuerySet and Manager
class CanvasCourseQuerySet(models.QuerySet):
    def with_enrollments(self):
        """Prefetch enrollments and their related students to avoid N+1 queries."""
        return self.prefetch_related('enrollments__student')
    
    def with_assignments(self):
        """Prefetch assignments to avoid N+1 queries."""
        return self.prefetch_related('assignments')
    
    def with_groups(self):
        """Prefetch group categories and groups."""
        return self.prefetch_related('group_categories__groups')
    
    def active(self):
        """Filter for active courses."""
        return self.filter(workflow_state='available')
    
    def published(self):
        """Filter for published courses."""
        return self.filter(workflow_state__in=['available', 'completed'])
    
    def current(self):
        """Filter for courses that are currently running."""
        now = timezone.now()
        return self.filter(
            models.Q(start_at__lte=now) | models.Q(start_at__isnull=True),
            models.Q(end_at__gte=now) | models.Q(end_at__isnull=True)
        )


class CanvasCourseManager(models.Manager):
    def get_queryset(self):
        return CanvasCourseQuerySet(self.model, using=self._db)
    
    def with_enrollments(self):
        return self.get_queryset().with_enrollments()
    
    def with_assignments(self):
        return self.get_queryset().with_assignments()
    
    def with_groups(self):
        return self.get_queryset().with_groups()
    
    def active(self):
        return self.get_queryset().active()
    
    def published(self):
        return self.get_queryset().published()
    
    def current(self):
        return self.get_queryset().current()


# CanvasEnrollment QuerySet and Manager
class CanvasEnrollmentQuerySet(models.QuerySet):
    def with_student_info(self):
        """Select related student to avoid N+1 queries."""
        return self.select_related('student')
    
    def with_course(self):
        """Select related course to avoid N+1 queries."""
        return self.select_related('course')
    
    def active(self):
        """Filter for active enrollments."""
        return self.filter(enrollment_state='active')
    
    def for_course(self, course):
        """Filter enrollments for a specific course."""
        return self.filter(course=course)
    
    def for_student(self, student):
        """Filter enrollments for a specific student."""
        return self.filter(student=student)
    
    def students_only(self):
        """Filter for student enrollments only."""
        return self.filter(role='StudentEnrollment')
    
    def teachers_only(self):
        """Filter for teacher enrollments only."""
        return self.filter(role='TeacherEnrollment')


class CanvasEnrollmentManager(models.Manager):
    def get_queryset(self):
        return CanvasEnrollmentQuerySet(self.model, using=self._db)
    
    def with_student_info(self):
        return self.get_queryset().with_student_info()
    
    def with_course(self):
        return self.get_queryset().with_course()
    
    def active(self):
        return self.get_queryset().active()
    
    def for_course(self, course):
        return self.get_queryset().for_course(course)
    
    def for_student(self, student):
        return self.get_queryset().for_student(student)
    
    def students_only(self):
        return self.get_queryset().students_only()
    
    def teachers_only(self):
        return self.get_queryset().teachers_only()


# CanvasAssignment QuerySet and Manager
class CanvasAssignmentQuerySet(models.QuerySet):
    def with_submissions(self):
        """Prefetch submissions with related enrollments and students."""
        return self.prefetch_related('submissions__enrollment__student')
    
    def with_course(self):
        """Select related course to avoid N+1 queries."""
        return self.select_related('course')
    
    def published(self):
        """Filter for published assignments."""
        return self.filter(published=True)
    
    def due_soon(self, days=7):
        """Filter for assignments due within the specified number of days."""
        future_date = timezone.now() + timedelta(days=days)
        return self.filter(
            due_at__isnull=False,
            due_at__lte=future_date,
            due_at__gte=timezone.now()
        )
    
    def past_due(self):
        """Filter for assignments that are past due."""
        return self.filter(
            due_at__isnull=False,
            due_at__lt=timezone.now()
        )
    
    def for_course(self, course):
        """Filter assignments for a specific course."""
        return self.filter(course=course)
    
    def needs_grading(self):
        """Filter for assignments that have submissions needing grading."""
        return self.filter(needs_grading_count__gt=0)


class CanvasAssignmentManager(models.Manager):
    def get_queryset(self):
        return CanvasAssignmentQuerySet(self.model, using=self._db)
    
    def with_submissions(self):
        return self.get_queryset().with_submissions()
    
    def with_course(self):
        return self.get_queryset().with_course()
    
    def published(self):
        return self.get_queryset().published()
    
    def due_soon(self, days=7):
        return self.get_queryset().due_soon(days)
    
    def past_due(self):
        return self.get_queryset().past_due()
    
    def for_course(self, course):
        return self.get_queryset().for_course(course)
    
    def needs_grading(self):
        return self.get_queryset().needs_grading()


# CanvasSubmission QuerySet and Manager
class CanvasSubmissionQuerySet(models.QuerySet):
    def with_full_details(self):
        """Select related enrollment, assignment, and student."""
        return self.select_related('enrollment__student', 'assignment__course')
    
    def for_assignment(self, assignment):
        """Filter submissions for a specific assignment."""
        return self.filter(assignment=assignment)
    
    def for_student(self, student):
        """Filter submissions for a specific student."""
        return self.filter(enrollment__student=student)
    
    def for_enrollment(self, enrollment):
        """Filter submissions for a specific enrollment."""
        return self.filter(enrollment=enrollment)
    
    def submitted(self):
        """Filter for submitted submissions."""
        return self.filter(workflow_state='submitted')
    
    def graded(self):
        """Filter for graded submissions."""
        return self.filter(workflow_state='graded')
    
    def late(self):
        """Filter for late submissions."""
        return self.filter(late=True)
    
    def missing(self):
        """Filter for missing submissions."""
        return self.filter(missing=True)


class CanvasSubmissionManager(models.Manager):
    def get_queryset(self):
        return CanvasSubmissionQuerySet(self.model, using=self._db)
    
    def with_full_details(self):
        return self.get_queryset().with_full_details()
    
    def for_assignment(self, assignment):
        return self.get_queryset().for_assignment(assignment)
    
    def for_student(self, student):
        return self.get_queryset().for_student(student)
    
    def for_enrollment(self, enrollment):
        return self.get_queryset().for_enrollment(enrollment)
    
    def submitted(self):
        return self.get_queryset().submitted()
    
    def graded(self):
        return self.get_queryset().graded()
    
    def late(self):
        return self.get_queryset().late()
    
    def missing(self):
        return self.get_queryset().missing()


# CanvasGroupCategory QuerySet and Manager
class CanvasGroupCategoryQuerySet(models.QuerySet):
    def with_groups(self):
        """Prefetch related groups to avoid N+1 queries."""
        return self.prefetch_related('groups')
    
    def with_memberships(self):
        """Prefetch groups with their memberships."""
        return self.prefetch_related('groups__memberships__student')
    
    def for_course(self, course):
        """Filter group categories for a specific course."""
        return self.filter(course=course)
    
    def self_signup_enabled(self):
        """Filter for group categories that allow self signup."""
        return self.filter(self_signup__in=['enabled', 'restricted'])


class CanvasGroupCategoryManager(models.Manager):
    def get_queryset(self):
        return CanvasGroupCategoryQuerySet(self.model, using=self._db)
    
    def with_groups(self):
        return self.get_queryset().with_groups()
    
    def with_memberships(self):
        return self.get_queryset().with_memberships()
    
    def for_course(self, course):
        return self.get_queryset().for_course(course)
    
    def self_signup_enabled(self):
        return self.get_queryset().self_signup_enabled()


# CanvasGroup QuerySet and Manager
class CanvasGroupQuerySet(models.QuerySet):
    def with_memberships(self):
        """Prefetch memberships with related students."""
        return self.prefetch_related('memberships__student')
    
    def with_category(self):
        """Select related category to avoid N+1 queries."""
        return self.select_related('category')
    
    def with_core_team(self):
        """Select related core team to avoid N+1 queries."""
        return self.select_related('core_team')
    
    def for_category(self, category):
        """Filter groups for a specific category."""
        return self.filter(category=category)
    
    def for_course(self, course):
        """Filter groups for a specific course."""
        return self.filter(category__course=course)
    
    def linked_to_team(self):
        """Filter groups that are linked to a core team."""
        return self.filter(core_team__isnull=False)


class CanvasGroupManager(models.Manager):
    def get_queryset(self):
        return CanvasGroupQuerySet(self.model, using=self._db)
    
    def with_memberships(self):
        return self.get_queryset().with_memberships()
    
    def with_category(self):
        return self.get_queryset().with_category()
    
    def with_core_team(self):
        return self.get_queryset().with_core_team()
    
    def for_category(self, category):
        return self.get_queryset().for_category(category)
    
    def for_course(self, course):
        return self.get_queryset().for_course(course)
    
    def linked_to_team(self):
        return self.get_queryset().linked_to_team()


# CanvasQuiz QuerySet and Manager
class CanvasQuizQuerySet(models.QuerySet):
    def with_assignment(self):
        """Select related assignment to avoid N+1 queries."""
        return self.select_related('assignment')
    
    def with_course(self):
        """Select related course to avoid N+1 queries."""
        return self.select_related('course')
    
    def published(self):
        """Filter for published quizzes."""
        return self.filter(published=True)
    
    def recent(self, days=30):
        """Filter for quizzes created in the last N days."""
        cutoff_date = timezone.now() - timedelta(days=days)
        return self.filter(created_at__gte=cutoff_date)
    
    def upcoming(self, days=7):
        """Filter for quizzes due within the next N days."""
        future_date = timezone.now() + timedelta(days=days)
        return self.filter(
            due_at__isnull=False,
            due_at__lte=future_date,
            due_at__gte=timezone.now()
        )
    
    def for_course(self, course):
        """Filter quizzes for a specific course."""
        return self.filter(course=course)
    
    def graded_quizzes(self):
        """Filter for graded quizzes (assignments)."""
        return self.filter(quiz_type='assignment')


class CanvasQuizManager(models.Manager):
    def get_queryset(self):
        return CanvasQuizQuerySet(self.model, using=self._db)
    
    def with_assignment(self):
        return self.get_queryset().with_assignment()
    
    def with_course(self):
        return self.get_queryset().with_course()
    
    def published(self):
        return self.get_queryset().published()
    
    def recent(self, days=30):
        return self.get_queryset().recent(days)
    
    def upcoming(self, days=7):
        return self.get_queryset().upcoming(days)
    
    def for_course(self, course):
        return self.get_queryset().for_course(course)
    
    def graded_quizzes(self):
        return self.get_queryset().graded_quizzes()