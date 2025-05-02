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
import httpx

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


def canvas_students_list(request):
    """View listing all Canvas students across all courses"""
    if not request.user.is_authenticated:
        return redirect('login')

    integration = get_integration_for_user(request.user)

    if not integration:
        return redirect('canvas_setup')

    # Get all enrollments that are students from all courses
    enrollments = CanvasEnrollment.objects.filter(
        course__integration=integration,
        role='StudentEnrollment'
    ).select_related('course')

    # Group by student
    students_by_id = {}
    for enrollment in enrollments:
        if enrollment.user_id not in students_by_id:
            students_by_id[enrollment.user_id] = {
                'user_id': enrollment.user_id,
                'name': enrollment.user_name,
                'email': enrollment.email,
                'courses': []
            }
        students_by_id[enrollment.user_id]['courses'].append({
            'course': enrollment.course,
            'enrollment': enrollment
        })

    context = {
        'integration': integration,
        'students': list(students_by_id.values()),
    }

    return render(request, 'canvas/students_list.html', context)


def canvas_assignments_list(request):
    """View listing all Canvas assignments across all courses"""
    if not request.user.is_authenticated:
        return redirect('login')

    integration = get_integration_for_user(request.user)

    if not integration:
        return redirect('canvas_setup')

    # Get all assignments from all courses
    assignments = CanvasAssignment.objects.filter(
        course__integration=integration
    ).select_related('course')

    # Group by course
    assignments_by_course = {}
    for assignment in assignments:
        course_id = assignment.course.id
        if course_id not in assignments_by_course:
            assignments_by_course[course_id] = {
                'course': assignment.course,
                'assignments': []
            }
        assignments_by_course[course_id]['assignments'].append(assignment)

    context = {
        'integration': integration,
        'assignments_by_course': list(assignments_by_course.values()),
    }

    return render(request, 'canvas/assignments_list.html', context)


def canvas_courses_list(request):
    """View listing all Canvas courses"""
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

    return render(request, 'canvas/courses_list.html', context)


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

    # For a direct URL access, we'll redirect to a page that shows progress
    # Initialize the sync in a background thread
    user_id = request.user.id
    import threading
    from .client import Client
    import asyncio
    from .progress import SyncProgress
    
    # Initialize progress tracking
    SyncProgress.start_sync(user_id, None, total_steps=10)  # Placeholder total, will be updated during sync
    
    def run_sync():
        client = Client(integration)
        try:
            synced_courses = asyncio.run(client.sync_all_courses(user_id))
            logger.info(f"Successfully synced {len(synced_courses)} courses from Canvas")
        except Exception as e:
            logger.error(f"Error syncing courses: {e}")
            # Update progress with error
            SyncProgress.complete_sync(
                user_id, 
                None, 
                success=False, 
                message="Sync failed with an error",
                error=str(e)
            )
    
    # Start the sync in a background thread
    sync_thread = threading.Thread(target=run_sync)
    sync_thread.daemon = True
    sync_thread.start()
    
    # Redirect to dashboard with message that sync has started
    messages.info(request, 'Syncing courses from Canvas. This may take a while. You can check progress below.')
    
    # Add a session flag to indicate sync is in progress
    request.session['canvas_sync_in_progress'] = True
    request.session['canvas_sync_started'] = True
    
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


def canvas_delete_course(request, course_id):
    """Delete a Canvas course and all related data"""
    if not request.user.is_authenticated:
        return redirect('login')

    integration = get_integration_for_user(request.user)
    if not integration:
        return redirect('canvas_setup')

    # Get the course
    course = get_object_or_404(
        CanvasCourse, canvas_id=course_id, integration=integration)

    if request.method == 'POST':
        # Get the course name for the success message
        course_name = f"{course.course_code}: {course.name}"

        # Delete the course (this will cascade delete related objects)
        course.delete()

        messages.success(
            request, f'Successfully removed course "{course_name}" from GradeBench.')
        return redirect('canvas_courses_list')

    # If it's a GET request, show confirmation page
    return render(request, 'canvas/confirm_delete_course.html', {
        'course': course,
    })


def canvas_sync_single_course(request, course_id):
    """Sync a single course from Canvas"""
    if not request.user.is_authenticated:
        return redirect('login')

    integration = get_integration_for_user(request.user)

    if not integration:
        messages.error(request, 'Canvas integration not set up')
        return redirect('canvas_setup')

    # Initialize the sync in a background thread
    user_id = request.user.id
    import threading
    from .client import Client
    import asyncio
    from .progress import SyncProgress
    
    # Initialize progress before starting the thread
    SyncProgress.start_sync(user_id, course_id)
    
    def run_sync():
        client = Client(integration)
        try:
            course = asyncio.run(client.sync_course(course_id, user_id))
            logger.info(f"Successfully synced course: {course.name}")
        except Exception as e:
            logger.error(f"Error syncing course {course_id}: {e}")
            # Update progress with error
            SyncProgress.complete_sync(
                user_id, 
                course_id, 
                success=False, 
                message="Course sync failed with an error.",
                error=str(e)
            )
    
    # Start the sync in a background thread
    sync_thread = threading.Thread(target=run_sync)
    sync_thread.daemon = True
    sync_thread.start()
    
    # Redirect with message that sync has started
    messages.info(request, 'Course sync has started. This may take a while. You can check progress below.')
    
    # Add a session flag to indicate sync is in progress
    request.session[f'canvas_sync_course_{course_id}_in_progress'] = True
    
    return redirect('canvas_course_detail', course_id=course_id)


@login_required
def canvas_list_available_courses(request):
    """
    Fetches the list of available Canvas courses for the authenticated user (preview only).
    """
    integration = get_integration_for_user(request.user)
    if not integration:
        return JsonResponse({'error': 'Canvas integration not set up'}, status=400)

    api_url = integration.canvas_url.rstrip(
        '/') + '/api/v1/courses?per_page=100&enrollment_state=active'
    headers = {
        'Authorization': f'Bearer {integration.api_key}',
    }
    all_courses = []
    url = api_url

    while url:
        resp = httpx.get(url, headers=headers)
        if resp.status_code != 200:
            return JsonResponse({'error': 'Failed to fetch courses from Canvas'}, status=resp.status_code)
        courses = resp.json()
        all_courses.extend(courses)
        # Handle pagination
        link = resp.headers.get('Link')
        next_url = None
        if link:
            for part in link.split(','):
                if 'rel="next"' in part:
                    next_url = part.split(';')[0].strip()[1:-1]
                    break
        url = next_url

    course_list = [
        {
            'id': c['id'],
            'name': c['name'],
            'course_code': c.get('course_code', ''),
            'start_at': c.get('start_at', ''),
            'end_at': c.get('end_at', ''),
            'workflow_state': c.get('workflow_state', ''),
        }
        for c in all_courses
    ]
    return JsonResponse({'courses': course_list})


@login_required
def canvas_sync_progress(request):
    """
    Get the current progress of a sync operation
    """
    from .progress import SyncProgress
    user_id = request.user.id
    course_id = request.GET.get('course_id')
    
    progress = SyncProgress.get(user_id, course_id)
    
    # If the status is completed or error, clear any session flags
    if course_id and progress.get('status') in [SyncProgress.STATUS_COMPLETED, SyncProgress.STATUS_ERROR]:
        session_key = f'canvas_sync_course_{course_id}_in_progress'
        if session_key in request.session:
            del request.session[session_key]
    elif not course_id and progress.get('status') in [SyncProgress.STATUS_COMPLETED, SyncProgress.STATUS_ERROR]:
        if 'canvas_sync_in_progress' in request.session:
            del request.session['canvas_sync_in_progress']
    
    return JsonResponse(progress)

@csrf_exempt
@require_POST
@login_required
def canvas_sync_selected_courses(request):
    """
    Sync only the selected Canvas courses. Expects a POST with JSON: { "course_ids": [123, 456, ...] }
    Uses AJAX with progress tracking for better UX.
    """
    import json
    integration = get_integration_for_user(request.user)
    if not integration:
        return JsonResponse({'error': 'Canvas integration not set up'}, status=400)

    try:
        data = json.loads(request.body)
        course_ids = data.get('course_ids', [])
        if not course_ids:
            return JsonResponse({
                'error': 'Please select at least one course to sync',
                'status': 'error'
            }, status=400)
    except Exception as e:
        return JsonResponse({
            'error': f'Invalid request format: {str(e)}',
            'status': 'error'
        }, status=400)

    # For AJAX, we're going to start the sync process asynchronously and 
    # immediately return a response to the client indicating that the 
    # sync has been started
    user_id = request.user.id
    
    # Start the sync in a background thread
    import threading
    from .client import Client
    import asyncio
    from .progress import SyncProgress
    
    # Initialize progress before starting the thread
    SyncProgress.start_sync(user_id, None, total_steps=len(course_ids))
    
    def run_sync():
        client = Client(integration)
        try:
            asyncio.run(sync_courses(client, course_ids, user_id))
        except Exception as e:
            # Handle any unexpected errors in the thread
            SyncProgress.complete_sync(user_id, None, success=False, error=str(e))
    
    async def sync_courses(client, course_ids, user_id):
        synced = []
        errors = []
        
        for i, course_id in enumerate(course_ids):
            try:
                # Update progress at the overall level
                SyncProgress.update(
                    user_id, 
                    None,
                    current=i, 
                    total=len(course_ids),
                    status="syncing_course",
                    message=f"Syncing course {i+1} of {len(course_ids)}"
                )
                
                # This will automatically update progress through the client
                course = await client.sync_course(course_id, user_id)
                synced.append(course_id)
            except Exception as e:
                errors.append({'course_id': course_id, 'error': str(e)})
        
        # Mark the overall sync as complete
        success = len(synced) > 0
        message = f"Completed sync of {len(synced)} out of {len(course_ids)} courses."
        error = None if success else "Failed to sync any courses"
        
        SyncProgress.complete_sync(
            user_id, 
            None,
            success=success,
            message=message,
            error=error
        )
    
    # Start the sync in a background thread
    sync_thread = threading.Thread(target=run_sync)
    sync_thread.daemon = True
    sync_thread.start()
    
    # Return immediately with a response that the sync has been started
    return JsonResponse({
        'status': 'started',
        'message': f'Started syncing {len(course_ids)} course(s)',
        'course_ids': course_ids
    })
