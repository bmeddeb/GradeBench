"""
Views for Canvas courses
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.db.models import Count, Q
from django.db import transaction
from django.http import JsonResponse
from django.contrib import messages

from ..models import (
    CanvasCourse,
    CanvasEnrollment,
    CanvasAssignment,
    CanvasSubmission,
    CanvasRubricCriterion,
)
from ..forms import CourseFilterForm
from ..decorators import canvas_integration_required, canvas_integration_required_json
from ..utils import get_json_error_response, get_json_success_response

logger = logging.getLogger(__name__)


@method_decorator(canvas_integration_required, name='dispatch')
class CourseListView(ListView):
    """Class-based view for listing Canvas courses"""
    template_name = "canvas/courses_list.html"
    context_object_name = "course_data"
    
    def get_queryset(self):
        """Get courses with annotated counts and apply filters"""
        integration = self.request.canvas_integration
        
        # Get filter form parameters
        form = self.get_filter_form()
        
        # Start with base queryset
        queryset = CanvasCourse.objects.filter(
            integration=integration
        )
        
        # Apply filters if the form is valid
        if form.is_valid():
            # Apply search filter
            search = form.cleaned_data.get('search')
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) | 
                    Q(course_code__icontains=search)
                )
            
            # Apply status filter
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(workflow_state=status)
        
        # Prefetch related data for more accurate counting
        courses = queryset.prefetch_related('enrollments', 'assignments')

        # Format the data to match what the template expects with proper counting
        course_data = []
        for course in courses:
            # Count only student enrollments, not all enrollments
            student_count = sum(1 for e in course.enrollments.all()
                               if e.role == "StudentEnrollment")

            course_data.append({
                'course': course,
                'enrollment_count': student_count,
                'assignment_count': course.assignments.count()
            })

        return course_data
        
    def get_filter_form(self):
        """Get and initialize the filter form"""
        return CourseFilterForm(self.request.GET or None)
    
    def get_context_data(self, **kwargs):
        """Add integration and quiz count to context"""
        context = super().get_context_data(**kwargs)
        integration = self.request.canvas_integration
        context['integration'] = integration
        
        # Add filter form to context
        context['filter_form'] = self.get_filter_form()
        
        # Count all quizzes across all courses
        try:
            from ..models import CanvasQuiz
            quiz_count = CanvasQuiz.objects.filter(course__integration=integration).count()
        except (ImportError, Exception):
            quiz_count = 0
        context['total_quizzes'] = quiz_count
        
        return context


@method_decorator(canvas_integration_required, name='dispatch')
class CourseDetailView(DetailView):
    """Class-based view for course details"""
    model = CanvasCourse
    template_name = "canvas/course_detail.html"
    context_object_name = "course"
    pk_url_kwarg = "course_id"
    
    def get_object(self, queryset=None):
        """Get course by canvas_id"""
        integration = self.request.canvas_integration
        return get_object_or_404(
            CanvasCourse, 
            canvas_id=self.kwargs.get(self.pk_url_kwarg),
            integration=integration
        )
    
    def get_context_data(self, **kwargs):
        """Get enrollments and assignments with statistics"""
        context = super().get_context_data(**kwargs)
        course = self.object
        
        # Get enrollments and assignments with prefetching
        enrollments = list(
            CanvasEnrollment.objects.filter(
                course=course
            ).order_by("role", "sortable_name")
        )
        
        assignments = list(
            CanvasAssignment.objects.filter(
                course=course
            ).order_by("position", "due_at")
        )
        
        # Calculate statistics
        student_count = len([e for e in enrollments if e.role == "StudentEnrollment"])
        instructor_count = len(
            [e for e in enrollments if e.role in ["TeacherEnrollment", "TaEnrollment"]]
        )
        
        context.update({
            "enrollments": enrollments,
            "assignments": assignments,
            "student_count": student_count,
            "instructor_count": instructor_count,
        })
        
        return context


@method_decorator(canvas_integration_required, name='dispatch')
class CourseDashboardView(ListView):
    """Dashboard view showing course statistics"""
    template_name = "canvas/dashboard.html"
    context_object_name = "course_data"
    
    def get_queryset(self):
        """Get courses with annotated counts"""
        integration = self.request.canvas_integration

        # Get courses with prefetched related data for more accurate counting
        courses = CanvasCourse.objects.filter(
            integration=integration
        ).prefetch_related('enrollments', 'assignments')

        # Format the data to match what the template expects with proper counting
        course_data = []
        for course in courses:
            # Count only student enrollments, not all enrollments
            student_count = sum(1 for e in course.enrollments.all()
                               if e.role == "StudentEnrollment")

            course_data.append({
                'course': course,
                'enrollment_count': student_count,
                'assignment_count': course.assignments.count()
            })

        return course_data
    
    def get_context_data(self, **kwargs):
        """Add integration and count metrics to context"""
        context = super().get_context_data(**kwargs)
        integration = self.request.canvas_integration
        context['integration'] = integration
        
        # Count all quiz assignments across all courses
        quiz_count = CanvasAssignment.objects.filter(
            course__integration=integration,
            is_quiz_assignment=True
        ).count()
        context['total_quizzes'] = quiz_count
        
        # Count all non-quiz assignments across all courses
        assignment_count = CanvasAssignment.objects.filter(
            course__integration=integration,
            is_quiz_assignment=False
        ).count()
        context['total_assignments'] = assignment_count
        
        return context


@canvas_integration_required
def canvas_delete_course(request, course_id):
    """Delete a Canvas course and all related data"""
    integration = request.canvas_integration
    
    # Get the course
    course = get_object_or_404(
        CanvasCourse, canvas_id=course_id, integration=integration
    )
    
    if request.method == "POST":
        # Get the course name for the success message
        course_name = f"{course.course_code}: {course.name}"
        
        # Delete the course (this will cascade delete related objects)
        course.delete()
        
        messages.success(
            request, f'Successfully removed course "{course_name}" from GradeBench.'
        )
        return redirect("canvas_courses_list")
    
    # If it's a GET request, show confirmation page
    return render(
        request,
        "canvas/confirm_delete_course.html",
        {
            "course": course,
        },
    )


# Function-based views for compatibility
canvas_courses_list = CourseListView.as_view()
course_detail = CourseDetailView.as_view()
canvas_dashboard = CourseDashboardView.as_view()