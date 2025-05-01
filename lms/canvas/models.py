from django.db import models
from core.models import Team, StudentProfile, UserProfile

class CanvasCourse(models.Model):
    """
    Mirrors a Canvas course
    """
    course_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    term = models.CharField(max_length=100, blank=True)
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name='canvas_courses'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.course_id})"

class CanvasEnrollment(models.Model):
    """
    Links a student to a Canvas course with a specific role
    """
    course = models.ForeignKey(
        CanvasCourse, on_delete=models.CASCADE, related_name='enrollments'
    )
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='canvas_enrollments'
    )
    role = models.CharField(max_length=30)  # e.g. 'StudentEnrollment', 'TeacherEnrollment'

    class Meta:
        unique_together = ('course', 'student')

    def __str__(self):
        return f"{self.student.user_profile.user.username} in {self.course.name} as {self.role}"

class CanvasAssignment(models.Model):
    """
    Mirrors a Canvas assignment
    """
    assignment_id = models.IntegerField(unique=True)
    course = models.ForeignKey(
        CanvasCourse, on_delete=models.CASCADE, related_name='assignments'
    )
    name = models.CharField(max_length=255)
    due_at = models.DateTimeField(null=True, blank=True)
    max_score = models.DecimalField(max_digits=6, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.assignment_id})"

class Rubric(models.Model):
    # Mirrors Canvas Rubric
    rubric_id = models.IntegerField(unique=True)
    title = models.CharField(max_length=255)
    points_possible = models.DecimalField(max_digits=8, decimal_places=2)
    reusable = models.BooleanField(default=False)
    read_only = models.BooleanField(default=False)
    free_form_criterion_comments = models.BooleanField(default=True)
    hide_score_total = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rubric {self.rubric_id}: {self.title}"

class RubricCriterion(models.Model):
    # Each criterion (row) in a Rubric
    rubric = models.ForeignKey(
        Rubric, on_delete=models.CASCADE, related_name='criteria'
    )
    criterion_id = models.CharField(max_length=50)
    description = models.TextField()
    long_description = models.TextField(blank=True, null=True)
    points = models.DecimalField(max_digits=8, decimal_places=2)
    criterion_use_range = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.rubric.title} - {self.description[:20]}..."

class RubricRating(models.Model):
    # Possible rating levels per criterion
    criterion = models.ForeignKey(
        RubricCriterion, on_delete=models.CASCADE, related_name='ratings'
    )
    rating_id = models.CharField(max_length=50)
    description = models.CharField(max_length=255)
    long_description = models.TextField(blank=True, null=True)
    points = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self):
        return f"{self.criterion.description[:15]} - {self.description}"

class RubricAssociation(models.Model):
    # Links a rubric to a course or assignment
    rubric = models.ForeignKey(
        Rubric, on_delete=models.CASCADE, related_name='associations'
    )
    course = models.ForeignKey(
        CanvasCourse, on_delete=models.CASCADE, related_name='rubric_associations', blank=True, null=True
    )
    assignment = models.ForeignKey(
        CanvasAssignment, on_delete=models.CASCADE, related_name='rubric_associations', blank=True, null=True
    )
    use_for_grading = models.BooleanField(default=True)
    purpose = models.CharField(max_length=50, default='grading')  # grading | bookmark
    hide_score_total = models.BooleanField(default=False)
    hide_points = models.BooleanField(default=False)
    hide_outcome_results = models.BooleanField(default=False)

    class Meta:
        unique_together = ('rubric', 'course', 'assignment')

    def __str__(self):
        target = self.assignment or self.course
        return f"Rubric {self.rubric.rubric_id} on {target}"

class RubricAssessment(models.Model):
    # Student's scored rubric submission
    rubric = models.ForeignKey(
        Rubric, on_delete=models.CASCADE, related_name='assessments'
    )
    association = models.ForeignKey(
        RubricAssociation, on_delete=models.CASCADE, related_name='assessments'
    )
    artifact_type = models.CharField(max_length=50, default='Submission')  # Submission | etc.
    artifact_id = models.IntegerField()
    artifact_attempt = models.IntegerField(default=1)
    assessment_type = models.CharField(max_length=50, default='grading')  # grading | peer_review | provisional
    assessor = models.ForeignKey(
        UserProfile, on_delete=models.SET_NULL, null=True, related_name='rubric_assessments'
    )
    student = models.ForeignKey(
        StudentProfile, on_delete=models.CASCADE, related_name='rubric_assessments'
    )
    score = models.DecimalField(max_digits=8, decimal_places=2)
    data = models.JSONField()      # Store full criterion-level data
    comments = models.JSONField()  # Comment-only view
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('association', 'student', 'assessor')

    def __str__(self):
        return f"Assessment for {self.student.user_profile.user.username} on {self.association}"