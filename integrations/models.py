from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from core.async_utils import AsyncModelMixin


class ProviderAssociation(models.Model, AsyncModelMixin):
    """
    Generic model for associating entities across different provider domains.
    
    This model creates a flexible way to link objects from different domains,
    such as Git repositories to project management projects, or LMS assignments
    to Git repositories.
    """
    # Source object (generic foreign key)
    source_content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        related_name='source_associations'
    )
    source_object_id = models.PositiveIntegerField()
    source = GenericForeignKey('source_content_type', 'source_object_id')
    
    # Target object (generic foreign key)
    target_content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        related_name='target_associations'
    )
    target_object_id = models.PositiveIntegerField()
    target = GenericForeignKey('target_content_type', 'target_object_id')
    
    # Association metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    association_type = models.CharField(max_length=100)
    metadata = models.JSONField(default=dict, blank=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['source_content_type', 'source_object_id']),
            models.Index(fields=['target_content_type', 'target_object_id']),
        ]
        verbose_name = "Provider Association"
        verbose_name_plural = "Provider Associations"
    
    def __str__(self):
        return f"{self.source} -> {self.target} ({self.association_type})"


class GradeLink(models.Model, AsyncModelMixin):
    """
    Connects student work in Git repositories to assignments in LMS.
    
    This model creates a specific association between student repositories,
    project management tasks, and LMS assignments for grading purposes.
    """
    # These fields would be proper foreign keys in the actual implementation
    # For now, we're keeping the CharField format from existing structure
    # These can be updated to proper FKs once the other models are established and tested
    lms_course_id = models.CharField(max_length=100)
    lms_assignment_id = models.CharField(max_length=100)
    git_repository_id = models.CharField(max_length=100)
    project_task_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Grading metadata
    student_id = models.CharField(max_length=100)
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by = models.CharField(max_length=100, blank=True)
    comments = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Grade Link"
        verbose_name_plural = "Grade Links"
    
    def __str__(self):
        return f"Grade for {self.student_id} - Assignment {self.lms_assignment_id}"
