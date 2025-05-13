"""
Views for Canvas quizzes
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.db.models import Prefetch, Count

from ..models import (
    CanvasCourse,
    CanvasQuiz,
    CanvasAssignment,
)
from ..decorators import canvas_integration_required

logger = logging.getLogger(__name__)


@method_decorator(canvas_integration_required, name='dispatch')
class QuizListView(ListView):
    """Class-based view for listing Canvas quizzes"""
    template_name = "canvas/quizzes_list.html"
    context_object_name = "quizzes_by_course"
    
    def get_queryset(self):
        """Get quizzes grouped by course"""
        integration = self.request.canvas_integration
        
        # Get all quizzes from all courses with related course data
        quizzes = CanvasQuiz.objects.filter(
            course__integration=integration
        ).select_related("course", "assignment")
        
        # Group by course
        quizzes_by_course = {}
        for quiz in quizzes:
            course_id = quiz.course.id
            if course_id not in quizzes_by_course:
                quizzes_by_course[course_id] = {
                    "course": quiz.course,
                    "quizzes": [],
                }
            quizzes_by_course[course_id]["quizzes"].append(quiz)
        
        return list(quizzes_by_course.values())
    
    def get_context_data(self, **kwargs):
        """Add integration to context"""
        context = super().get_context_data(**kwargs)
        context['integration'] = self.request.canvas_integration
        return context


@method_decorator(canvas_integration_required, name='dispatch')
class QuizDetailView(DetailView):
    """Class-based view for quiz details"""
    template_name = "canvas/quiz_detail.html"
    context_object_name = "quiz"
    
    def get_object(self, queryset=None):
        """Get quiz by ID and course ID"""
        integration = self.request.canvas_integration
        course = get_object_or_404(
            CanvasCourse, 
            canvas_id=self.kwargs.get('course_id'),
            integration=integration
        )
        
        return get_object_or_404(
            CanvasQuiz, 
            canvas_id=self.kwargs.get('quiz_id'), 
            course=course
        )
    
    def get_context_data(self, **kwargs):
        """Get quiz details and related information"""
        context = super().get_context_data(**kwargs)
        quiz = self.object
        course = quiz.course
        
        # Get related assignment if it exists
        assignment = quiz.assignment
        
        # Get assignment statistics if there's a linked assignment
        assignment_stats = None
        if assignment:
            submissions_count = assignment.submissions.count()
            submitted_count = assignment.submissions.filter(workflow_state="submitted").count()
            graded_count = assignment.submissions.filter(workflow_state="graded").count()
            missing_count = assignment.submissions.filter(missing=True).count()
            late_count = assignment.submissions.filter(late=True).count()
            
            assignment_stats = {
                "submissions_count": submissions_count,
                "submitted_count": submitted_count,
                "graded_count": graded_count,
                "missing_count": missing_count,
                "late_count": late_count,
            }
        
        context.update({
            "course": course,
            "quiz": quiz,
            "assignment": assignment,
            "assignment_stats": assignment_stats,
            "quiz_type_display": dict(CanvasQuiz.QUIZ_TYPES).get(quiz.quiz_type, quiz.quiz_type),
        })
        
        return context


# Function-based views for compatibility
canvas_quizzes_list = QuizListView.as_view()
quiz_detail = QuizDetailView.as_view()