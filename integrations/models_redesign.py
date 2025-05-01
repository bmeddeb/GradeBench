from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from core.async_utils import AsyncModelMixin
from core.models_redesign import Student

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
    Connects student work in Git repositories to assignments in LMS for grading.
    """
    # Student this grade is for
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='grade_links'
    )
    
    # LMS assignment reference
    course_id = models.CharField(max_length=100)
    assignment_id = models.CharField(max_length=100)
    
    # Source of work being graded
    git_repository_id = models.CharField(max_length=100, blank=True, null=True)
    project_task_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Grading metadata
    grade = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    graded_by_username = models.CharField(max_length=100, blank=True)
    comments = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Grade Link"
        verbose_name_plural = "Grade Links"
        unique_together = ('student', 'course_id', 'assignment_id')
    
    def __str__(self):
        return f"Grade for {self.student.full_name} - Assignment {self.assignment_id}"

    async def async_submit_to_canvas(self):
        """
        Submit this grade to Canvas via the Canvas API
        
        Returns:
            bool: True if submission was successful
        """
        # This would be implemented with an async call to the Canvas API
        # For now, just a placeholder
        from asgiref.sync import sync_to_async
        import asyncio
        
        # Simulate API call
        await asyncio.sleep(0.5)
        
        # Update the local record
        self.graded_at = await sync_to_async(lambda: timezone.now())()
        await self.async_save()
        
        return True
