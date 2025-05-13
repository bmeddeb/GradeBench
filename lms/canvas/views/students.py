"""
Views for Canvas students
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.db.models import Prefetch

from ..models import (
    CanvasCourse,
    CanvasEnrollment,
    CanvasAssignment,
    CanvasSubmission,
    CanvasGroupMembership,
)
from ..decorators import canvas_integration_required

logger = logging.getLogger(__name__)


@method_decorator(canvas_integration_required, name='dispatch')
class StudentListView(ListView):
    """Class-based view for listing Canvas students"""
    template_name = "canvas/students_list.html"
    context_object_name = "students"

    def get_queryset(self):
        """Get students grouped by user_id with their group memberships"""
        integration = self.request.canvas_integration

        # Get all enrollments that are students from all courses
        enrollments = CanvasEnrollment.objects.filter(
            course__integration=integration,
            role="StudentEnrollment"
        ).select_related("course")

        # Group by student
        students_by_id = {}
        for enrollment in enrollments:
            if enrollment.user_id not in students_by_id:
                students_by_id[enrollment.user_id] = {
                    "user_id": enrollment.user_id,
                    "name": enrollment.user_name,
                    "email": enrollment.email,
                    "courses": [],
                    "groups": [],  # New field to store group memberships
                }
            students_by_id[enrollment.user_id]["courses"].append(
                {"course": enrollment.course, "enrollment": enrollment}
            )

        # Get group memberships for each student
        if students_by_id:
            user_ids = list(students_by_id.keys())
            memberships = CanvasGroupMembership.objects.filter(
                user_id__in=user_ids,
                group__category__course__integration=integration
            ).select_related('group', 'group__category', 'group__category__course')

            # Add group memberships to each student's data
            for membership in memberships:
                if membership.user_id in students_by_id:
                    group_info = {
                        "id": membership.group.id,
                        "canvas_id": membership.group.canvas_id,
                        "name": membership.group.name,
                        "category_name": membership.group.category.name,
                        "category_id": membership.group.category.id,  # Use the internal DB ID, not canvas_id
                        "category_canvas_id": membership.group.category.canvas_id,  # Keep this for reference
                        "course_id": membership.group.category.course.canvas_id,
                        "course_code": membership.group.category.course.course_code
                    }
                    students_by_id[membership.user_id]["groups"].append(group_info)
        
        return list(students_by_id.values())
    
    def get_context_data(self, **kwargs):
        """Add integration to context"""
        context = super().get_context_data(**kwargs)
        context['integration'] = self.request.canvas_integration
        return context


@method_decorator(canvas_integration_required, name='dispatch')
class StudentDetailView(DetailView):
    """Class-based view for student details within a course"""
    template_name = "canvas/student_detail.html"
    context_object_name = "enrollment"
    
    def get_object(self, queryset=None):
        """Get student enrollment"""
        integration = self.request.canvas_integration
        course = get_object_or_404(CanvasCourse, canvas_id=self.kwargs.get('course_id'))
        
        # Check if user has access to this course
        if course.integration != integration:
            return None
        
        return get_object_or_404(
            CanvasEnrollment, 
            course=course, 
            user_id=self.kwargs.get('user_id')
        )
    
    def get(self, request, *args, **kwargs):
        """Handle unauthorized access"""
        self.object = self.get_object()
        if self.object is None:
            # Redirect if not authorized
            from django.contrib import messages
            messages.error(request, "You do not have access to this course")
            return redirect("canvas_dashboard")
            
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)
    
    def get_context_data(self, **kwargs):
        """Get submissions and statistics"""
        context = super().get_context_data(**kwargs)
        enrollment = self.object
        course = enrollment.course
        
        # Get all submissions for this student in this course with prefetch
        submissions = list(
            CanvasSubmission.objects.filter(
                enrollment=enrollment
            ).select_related(
                "assignment"  # Pre-fetch related assignments
            )
        )
        
        # Get submission statistics
        assignment_count = CanvasAssignment.objects.filter(course=course).count()
        submitted_count = len(
            [s for s in submissions if s.workflow_state in ["submitted", "graded"]]
        )
        missing_count = len([s for s in submissions if s.missing])
        late_count = len([s for s in submissions if s.late])
        
        # Calculate overall grade if available
        grades = enrollment.grades or {}
        current_score = grades.get("current_score")
        final_score = grades.get("final_score")
        
        context.update({
            "course": course,
            "submissions": submissions,
            "assignment_count": assignment_count,
            "submitted_count": submitted_count,
            "missing_count": missing_count,
            "late_count": late_count,
            "current_score": current_score,
            "final_score": final_score,
        })
        
        return context


# Function-based views for compatibility
canvas_students_list = StudentListView.as_view()
student_detail = StudentDetailView.as_view()