"""
Views for Canvas assignments
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.db.models import Prefetch, Count

from ..models import (
    CanvasCourse,
    CanvasAssignment,
    CanvasSubmission,
    CanvasRubricCriterion,
    CanvasRubric,
)
from ..decorators import canvas_integration_required

logger = logging.getLogger(__name__)


@method_decorator(canvas_integration_required, name='dispatch')
class AssignmentListView(ListView):
    """Class-based view for listing Canvas assignments"""
    template_name = "canvas/assignments_list.html"
    context_object_name = "assignments_by_course"
    
    def get_queryset(self):
        """Get assignments grouped by course"""
        integration = self.request.canvas_integration
        
        # Get all assignments from all courses with related course data
        assignments = CanvasAssignment.objects.filter(
            course__integration=integration
        ).select_related("course")
        
        # Group by course
        assignments_by_course = {}
        for assignment in assignments:
            course_id = assignment.course.id
            if course_id not in assignments_by_course:
                assignments_by_course[course_id] = {
                    "course": assignment.course,
                    "assignments": [],
                }
            assignments_by_course[course_id]["assignments"].append(assignment)
        
        return list(assignments_by_course.values())
    
    def get_context_data(self, **kwargs):
        """Add integration to context"""
        context = super().get_context_data(**kwargs)
        context['integration'] = self.request.canvas_integration
        return context


@method_decorator(canvas_integration_required, name='dispatch')
class AssignmentDetailView(DetailView):
    """Class-based view for assignment details"""
    template_name = "canvas/assignment_detail.html"
    context_object_name = "assignment"
    
    def get_object(self, queryset=None):
        """Get assignment by ID and course ID"""
        integration = self.request.canvas_integration
        course = get_object_or_404(
            CanvasCourse, 
            canvas_id=self.kwargs.get('course_id'),
            integration=integration
        )
        
        return get_object_or_404(
            CanvasAssignment, 
            canvas_id=self.kwargs.get('assignment_id'), 
            course=course
        )
    
    def get_context_data(self, **kwargs):
        """Get submissions and rubric information"""
        context = super().get_context_data(**kwargs)
        assignment = self.object
        course = assignment.course
        
        # Get all submissions for this assignment with related enrollments
        submissions = list(
            CanvasSubmission.objects.filter(
                assignment=assignment
            ).select_related(
                "enrollment"  # Pre-fetch related enrollments
            )
        )
        
        # Get statistics
        submitted_count = len([s for s in submissions if s.workflow_state == "submitted"])
        graded_count = len([s for s in submissions if s.workflow_state == "graded"])
        missing_count = len([s for s in submissions if s.missing])
        late_count = len([s for s in submissions if s.late])
        
        # Check if there's a rubric
        has_rubric = False
        rubric = None
        
        try:
            rubric_criteria = list(
                CanvasRubricCriterion.objects.filter(
                    rubric__in=list(
                        CanvasRubric.objects.filter(
                            canvas_id__in=list(
                                assignment.rubric_set.values_list(
                                    "canvas_id", flat=True
                                )
                            )
                        )
                    )
                ).prefetch_related("ratings")
            )
            
            if rubric_criteria:
                has_rubric = True
                rubric = {
                    "criteria": rubric_criteria,
                }
        except Exception as e:
            logger.error(f"Error fetching rubric: {str(e)}")
        
        context.update({
            "course": course,
            "submissions": submissions,
            "submitted_count": submitted_count,
            "graded_count": graded_count,
            "missing_count": missing_count,
            "late_count": late_count,
            "has_rubric": has_rubric,
            "rubric": rubric,
        })
        
        return context


# Function-based views for compatibility
canvas_assignments_list = AssignmentListView.as_view()
assignment_detail = AssignmentDetailView.as_view()