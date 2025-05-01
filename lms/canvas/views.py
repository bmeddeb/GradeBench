import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import sync_to_async
from django.db.models import Q, Count

from .models import (
    CanvasIntegration, CanvasCourse, CanvasEnrollment,
    CanvasAssignment, CanvasSubmission
)
from .client import Client

logger = logging.getLogger(__name__)

# Helper functions


def get_integration_for_user(user):
    """Get or create a Canvas integration for the user"""
    try:
        integration = CanvasIntegration.objects.get(user=user)
        return integration
    except CanvasIntegration.DoesNotExist:
        return None

# Synchronous views


def canvas_dashboard(request):
    """Dashboard showing Canvas courses and related information"""
    if not request.user.is_authenticated:
        return redirect('login')

    integration = get_integration_for_user(request.user)

    if not integration:
        return redirect('canvas_setup')

    # Get courses from database
    courses = list(CanvasCourse.objects.filter(integration=integration))

    # For each course, fetch enrollment and assignment counts
    course_data = []
    for course in courses:
        enrollment_count = CanvasEnrollment.objects.filter(
            course=course, role='StudentEnrollment').count()
        assignment_count = CanvasAssignment.objects.filter(
            course=course).count()

        course_data.append({
            'course': course,
            'enrollment_count': enrollment_count,
            'assignment_count': assignment_count
        })

    context = {
        'integration': integration,
        'course_data': course_data,
    }

    return render(request, 'canvas/dashboard.html', context)


def canvas_setup(request):
    """Set up Canvas API integration"""
    if not request.user.is_authenticated:
        return redirect('login')

    integration = get_integration_for_user(request.user)

    if request.method == 'POST':
        api_key = request.POST.get('api_key')
        canvas_url = request.POST.get(
            'canvas_url', 'https://canvas.instructure.com')

        if not api_key:
            messages.error(request, 'API Key is required')
            return render(request, 'canvas/setup.html', {'integration': integration})

        # Create or update the integration
        if integration:
            integration.api_key = api_key
            integration.canvas_url = canvas_url
            integration.save()
        else:
            integration = CanvasIntegration(
                user=request.user,
                api_key=api_key,
                canvas_url=canvas_url
            )
            integration.save()

        messages.success(request, 'Canvas integration set up successfully')
        return redirect('canvas_dashboard')

    return render(request, 'canvas/setup.html', {'integration': integration})


def canvas_sync(request):
    """Sync courses from Canvas"""
    if not request.user.is_authenticated:
        return redirect('login')

    integration = get_integration_for_user(request.user)

    if not integration:
        messages.error(request, 'Canvas integration not set up')
        return redirect('canvas_setup')

    try:
        client = Client(integration)
        # The client.sync_all_courses method is already async, so don't use sync_to_async
        import asyncio
        synced_courses = asyncio.run(client.sync_all_courses())
        messages.success(
            request, f'Successfully synced {len(synced_courses)} courses from Canvas')
    except Exception as e:
        logger.error(f"Error syncing courses: {e}")
        messages.error(request, f'Error syncing courses: {str(e)}')

    return redirect('canvas_dashboard')


def course_detail(request, course_id):
    """View a single Canvas course with enrollments and assignments"""
    if not request.user.is_authenticated:
        return redirect('login')

    course = get_object_or_404(CanvasCourse, canvas_id=course_id)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        messages.error(request, 'You do not have access to this course')
        return redirect('canvas_dashboard')

    # Get enrollments and assignments
    enrollments = list(
        CanvasEnrollment.objects.filter(course=course)
        .order_by('role', 'sortable_name')
    )

    assignments = list(
        CanvasAssignment.objects.filter(course=course)
        .order_by('position', 'due_at')
    )

    # Get some statistics
    student_count = len(
        [e for e in enrollments if e.role == 'StudentEnrollment'])
    instructor_count = len([e for e in enrollments if e.role in [
                           'TeacherEnrollment', 'TaEnrollment']])

    context = {
        'course': course,
        'enrollments': enrollments,
        'assignments': assignments,
        'student_count': student_count,
        'instructor_count': instructor_count,
    }

    return render(request, 'canvas/course_detail.html', context)


def assignment_detail(request, course_id, assignment_id):
    """View a single assignment with submissions"""
    if not request.user.is_authenticated:
        return redirect('login')

    course = get_object_or_404(CanvasCourse, canvas_id=course_id)
    assignment = get_object_or_404(
        CanvasAssignment, canvas_id=assignment_id, course=course)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        messages.error(request, 'You do not have access to this course')
        return redirect('canvas_dashboard')

    # Get all submissions for this assignment
    submissions = list(
        CanvasSubmission.objects.filter(assignment=assignment)
        .select_related('enrollment')  # Pre-fetch related enrollments
    )

    # Get statistics
    submitted_count = len(
        [s for s in submissions if s.workflow_state == 'submitted'])
    graded_count = len(
        [s for s in submissions if s.workflow_state == 'graded'])
    missing_count = len([s for s in submissions if s.missing])
    late_count = len([s for s in submissions if s.late])

    # Check if there's a rubric
    has_rubric = False
    rubric = None

    try:
        from .models import CanvasRubric
        rubric_criteria = list(
            CanvasRubricCriterion.objects.filter(
                rubric__in=list(
                    CanvasRubric.objects.filter(
                        canvas_id__in=list(
                            assignment.rubric_set.values_list(
                                'canvas_id', flat=True)
                        )
                    )
                )
            ).prefetch_related('ratings')
        )

        if rubric_criteria:
            has_rubric = True
            rubric = {
                'criteria': rubric_criteria,
            }
    except:
        pass

    context = {
        'course': course,
        'assignment': assignment,
        'submissions': submissions,
        'submitted_count': submitted_count,
        'graded_count': graded_count,
        'missing_count': missing_count,
        'late_count': late_count,
        'has_rubric': has_rubric,
        'rubric': rubric,
    }

    return render(request, 'canvas/assignment_detail.html', context)


def student_detail(request, course_id, user_id):
    """View a single student's information and submissions"""
    if not request.user.is_authenticated:
        return redirect('login')

    course = get_object_or_404(CanvasCourse, canvas_id=course_id)
    enrollment = get_object_or_404(
        CanvasEnrollment, course=course, user_id=user_id)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        messages.error(request, 'You do not have access to this course')
        return redirect('canvas_dashboard')

    # Get all submissions for this student in this course
    submissions = list(
        CanvasSubmission.objects.filter(enrollment=enrollment)
        .select_related('assignment')  # Pre-fetch related assignments
    )

    # Get submission statistics
    assignment_count = CanvasAssignment.objects.filter(course=course).count()
    submitted_count = len(
        [s for s in submissions if s.workflow_state in ['submitted', 'graded']])
    missing_count = len([s for s in submissions if s.missing])
    late_count = len([s for s in submissions if s.late])

    # Calculate overall grade if available
    grades = enrollment.grades or {}
    current_score = grades.get('current_score')
    final_score = grades.get('final_score')

    context = {
        'course': course,
        'enrollment': enrollment,
        'submissions': submissions,
        'assignment_count': assignment_count,
        'submitted_count': submitted_count,
        'missing_count': missing_count,
        'late_count': late_count,
        'current_score': current_score,
        'final_score': final_score,
    }

    return render(request, 'canvas/student_detail.html', context)


def sync_single_course(request, course_id):
    """Sync a single course from Canvas"""
    if not request.user.is_authenticated:
        return redirect('login')

    integration = get_integration_for_user(request.user)

    if not integration:
        messages.error(request, 'Canvas integration not set up')
        return redirect('canvas_setup')

    try:
        client = Client(integration)
        # The client.sync_course method is already async, so don't use sync_to_async
        import asyncio
        course = asyncio.run(client.sync_course(course_id))
        messages.success(request, f'Successfully synced course: {course.name}')
    except Exception as e:
        logger.error(f"Error syncing course {course_id}: {e}")
        messages.error(request, f'Error syncing course: {str(e)}')

    return redirect('canvas_course_detail', course_id=course_id)
