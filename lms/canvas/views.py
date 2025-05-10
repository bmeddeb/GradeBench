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
from .syncer import CanvasSyncer
from core.models import Team, Student

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
    """View listing all Canvas students across all courses with team information"""
    if not request.user.is_authenticated:
        return redirect('login')

    integration = get_integration_for_user(request.user)

    if not integration:
        return redirect('canvas_setup')

    # Get all enrollments that are students from all courses
    enrollments = CanvasEnrollment.objects.filter(
        course__integration=integration,
        role='StudentEnrollment'
    ).select_related('course', 'student', 'student__team')

    # Group by student
    students_by_id = {}
    for enrollment in enrollments:
        if enrollment.user_id not in students_by_id:
            # Create entry for student
            students_by_id[enrollment.user_id] = {
                'user_id': enrollment.user_id,
                'name': enrollment.user_name,
                'email': enrollment.email,
                'courses': [],
                'teams': {},  # Dictionary of teams by course ID for this student
                'has_team': False,  # Flag to indicate if student has any team
            }

        # Add course information
        students_by_id[enrollment.user_id]['courses'].append({
            'course': enrollment.course,
            'enrollment': enrollment
        })

        # Add team information if available
        if enrollment.student and enrollment.student.team:
            team = enrollment.student.team
            course_id = enrollment.course.id

            # Store team info for this course
            students_by_id[enrollment.user_id]['teams'][course_id] = {
                'team': team,
                'source': 'Canvas' if team.canvas_group_id else 'Manual',
                'course': enrollment.course
            }

            # Flag that student has at least one team
            students_by_id[enrollment.user_id]['has_team'] = True

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
    import asyncio
    from .progress import SyncProgress

    # Initialize progress tracking
    SyncProgress.start_sync(user_id, None, total_steps=10)  # Placeholder total, will be updated during sync

    def run_sync():
        client = Client(integration)
        syncer = CanvasSyncer(client)
        try:
            synced_courses = asyncio.run(syncer.sync_all_courses(user_id))
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
    """View a single Canvas course with enrollments, assignments and teams"""
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
        .select_related('student')  # Eager load student relationship
        .order_by('role', 'sortable_name')
    )

    assignments = list(
        CanvasAssignment.objects.filter(course=course)
        .order_by('position', 'due_at')
    )

    # Get teams for this course
    teams = list(
        Team.objects.filter(canvas_course=course)
        .annotate(student_count=Count('students'))
        .order_by('name')
    )

    # Get some statistics
    student_count = len(
        [e for e in enrollments if e.role == 'StudentEnrollment'])
    instructor_count = len([e for e in enrollments if e.role in [
                           'TeacherEnrollment', 'TaEnrollment']])

    # Calculate team statistics
    canvas_teams_count = len([t for t in teams if t.canvas_group_id is not None])
    manual_teams_count = len([t for t in teams if t.canvas_group_id is None])
    students_in_teams_count = sum(t.student_count for t in teams)

    # Check if any students don't have teams
    students_without_teams = student_count - students_in_teams_count

    context = {
        'course': course,
        'enrollments': enrollments,
        'assignments': assignments,
        'teams': teams,
        'student_count': student_count,
        'instructor_count': instructor_count,
        'canvas_teams_count': canvas_teams_count,
        'manual_teams_count': manual_teams_count,
        'students_in_teams_count': students_in_teams_count,
        'students_without_teams_count': students_without_teams,
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
    """View a single student's information, submissions, and team details"""
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

    # Get student and team information
    student = enrollment.student
    team = None
    team_members = []
    team_source = None

    if student and student.team:
        team = student.team
        team_source = "Canvas" if team.canvas_group_id else "Manual"

        # Get other team members
        team_members = list(
            Student.objects.filter(team=team)
            .exclude(id=student.id)
            .order_by('first_name', 'last_name')
        )

    context = {
        'course': course,
        'enrollment': enrollment,
        'student': student,
        'team': team,
        'team_source': team_source,
        'team_members': team_members,
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
    import asyncio
    from .progress import SyncProgress

    # Initialize progress before starting the thread
    SyncProgress.start_sync(user_id, course_id)

    def run_sync():
        client = Client(integration)
        syncer = CanvasSyncer(client)
        try:
            course = asyncio.run(syncer.sync_course(course_id, user_id))
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


def manage_teams(request, course_id):
    """View for managing teams and assigning students to teams with drag-and-drop interface"""
    if not request.user.is_authenticated:
        return redirect('login')

    course = get_object_or_404(CanvasCourse, canvas_id=course_id)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        messages.error(request, 'You do not have access to this course')
        return redirect('canvas_dashboard')

    # Get student enrollments with team information
    enrollments = list(
        CanvasEnrollment.objects.filter(
            course=course,
            role='StudentEnrollment'
        ).select_related('student')
        .order_by('sortable_name')
    )

    # Get all teams for this course
    teams = list(
        Team.objects.filter(canvas_course=course)
        .annotate(student_count=Count('students'))
        .order_by('name')
    )

    # Get client for making API calls
    client = Client(integration)
    syncer = CanvasSyncer(client)

    # Get unassigned students
    student_ids_with_teams = set()
    for team in teams:
        for student in team.students.all():
            student_ids_with_teams.add(student.id)

    unassigned_students = []
    for enrollment in enrollments:
        if enrollment.student and enrollment.student.id not in student_ids_with_teams:
            unassigned_students.append(enrollment.student)
        elif not enrollment.student:
            # Create student object for enrollments without one
            student = Student.objects.create(
                first_name=enrollment.user_name.split()[0] if ' ' in enrollment.user_name else enrollment.user_name,
                last_name=' '.join(enrollment.user_name.split()[1:]) if ' ' in enrollment.user_name else '',
                email=enrollment.email or f"canvas_{enrollment.user_id}@example.com",
                canvas_user_id=enrollment.user_id,
                created_by=request.user
            )
            enrollment.student = student
            enrollment.save()
            unassigned_students.append(student)

    # Get Canvas group categories
    import asyncio
    group_categories = asyncio.run(client.get_group_categories(course_id))

    context = {
        'course': course,
        'teams': teams,
        'unassigned_students': unassigned_students,
        'group_categories': group_categories,
    }

    return render(request, 'canvas/manage_teams.html', context)


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
def create_team(request, course_id):
    """
    Create a new team for the course.
    Expects a POST with JSON: { "name": "Team Name", "description": "Description" }
    """
    import json
    course = get_object_or_404(CanvasCourse, canvas_id=course_id)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        return JsonResponse({'error': 'You do not have access to this course'}, status=403)

    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        description = data.get('description', '').strip()
        category_id = data.get('category_id')
        push_to_canvas = data.get('push_to_canvas', False)

        if not name:
            return JsonResponse({'error': 'Team name is required'}, status=400)

    except Exception as e:
        return JsonResponse({'error': f'Invalid request format: {str(e)}'}, status=400)

    # Create the team in the database
    team = Team.objects.create(
        name=name,
        description=description,
        canvas_course=course,
        created_at=timezone.now()
    )

    # If specified, push to Canvas
    if push_to_canvas and category_id:
        client = Client(integration)

        # Run in a background thread to avoid blocking
        import threading
        import asyncio

        def push_team_to_canvas():
            try:
                # Create group in Canvas
                result = asyncio.run(client.create_group(
                    category_id=category_id,
                    name=name,
                    description=description
                ))

                # Update team with Canvas group ID
                if result and 'id' in result:
                    team.canvas_group_id = result['id']
                    team.last_synced_at = timezone.now()
                    team.save()
            except Exception as e:
                logger.error(f"Error creating Canvas group: {e}")

        # Start thread
        push_thread = threading.Thread(target=push_team_to_canvas)
        push_thread.daemon = True
        push_thread.start()

    return JsonResponse({
        'status': 'success',
        'team': {
            'id': team.id,
            'name': team.name,
            'description': team.description,
            'student_count': 0,
            'canvas_group_id': team.canvas_group_id
        }
    })


@csrf_exempt
@require_POST
@login_required
def assign_student_to_team(request):
    """
    Assign a student to a team.
    Expects a POST with JSON: { "student_id": 123, "team_id": 456 }
    """
    import json
    integration = get_integration_for_user(request.user)
    if not integration:
        return JsonResponse({'error': 'Canvas integration not set up'}, status=400)

    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')
        team_id = data.get('team_id')

        if not student_id or not team_id:
            return JsonResponse({'error': 'Student ID and Team ID are required'}, status=400)

    except Exception as e:
        return JsonResponse({'error': f'Invalid request format: {str(e)}'}, status=400)

    try:
        student = Student.objects.get(id=student_id)
        team = Team.objects.get(id=team_id)

        # Check if user has access to the course this team belongs to
        if team.canvas_course and team.canvas_course.integration != integration:
            return JsonResponse({'error': 'You do not have access to this team'}, status=403)

        # Update the student's team
        old_team = student.team
        student.team = team
        student.save()

        # If the team has a Canvas group_id, update in Canvas
        if team.canvas_group_id:
            client = Client(integration)

            # Run in a background thread to avoid blocking
            import threading
            import asyncio

            def update_canvas_group():
                try:
                    # Get all student IDs for this team
                    canvas_user_ids = list(
                        Student.objects.filter(team=team)
                        .exclude(canvas_user_id__isnull=True)
                        .values_list('canvas_user_id', flat=True)
                    )

                    # Update group membership in Canvas
                    asyncio.run(client.set_group_members(
                        group_id=team.canvas_group_id,
                        user_ids=canvas_user_ids
                    ))

                    # Update last sync timestamp
                    team.last_synced_at = timezone.now()
                    team.save()
                except Exception as e:
                    logger.error(f"Error updating Canvas group members: {e}")

            # Start thread
            update_thread = threading.Thread(target=update_canvas_group)
            update_thread.daemon = True
            update_thread.start()

        return JsonResponse({
            'status': 'success',
            'student': {
                'id': student.id,
                'name': student.full_name,
                'email': student.email
            },
            'team': {
                'id': team.id,
                'name': team.name
            },
            'old_team': {
                'id': old_team.id if old_team else None,
                'name': old_team.name if old_team else None
            } if old_team else None
        })
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    except Team.DoesNotExist:
        return JsonResponse({'error': 'Team not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Failed to assign student to team: {str(e)}'}, status=500)


@csrf_exempt
@require_POST
@login_required
def remove_student_from_team(request):
    """
    Remove a student from their team.
    Expects a POST with JSON: { "student_id": 123 }
    """
    import json
    integration = get_integration_for_user(request.user)
    if not integration:
        return JsonResponse({'error': 'Canvas integration not set up'}, status=400)

    try:
        data = json.loads(request.body)
        student_id = data.get('student_id')

        if not student_id:
            return JsonResponse({'error': 'Student ID is required'}, status=400)

    except Exception as e:
        return JsonResponse({'error': f'Invalid request format: {str(e)}'}, status=400)

    try:
        student = Student.objects.get(id=student_id)

        # Only allow removing if student has a team
        if not student.team:
            return JsonResponse({'error': 'Student is not assigned to any team'}, status=400)

        # Check if user has access to the course this team belongs to
        team = student.team
        if team.canvas_course and team.canvas_course.integration != integration:
            return JsonResponse({'error': 'You do not have access to this team'}, status=403)

        # Remember the team for response
        old_team = {
            'id': team.id,
            'name': team.name,
            'canvas_group_id': team.canvas_group_id
        }

        # Update Canvas if needed
        if team.canvas_group_id:
            client = Client(integration)

            # Run in a background thread to avoid blocking
            import threading
            import asyncio

            def update_canvas_group():
                try:
                    # Get remaining students after removal
                    canvas_user_ids = list(
                        Student.objects.filter(team=team)
                        .exclude(id=student.id)  # Exclude the one being removed
                        .exclude(canvas_user_id__isnull=True)
                        .values_list('canvas_user_id', flat=True)
                    )

                    # Update group membership in Canvas
                    asyncio.run(client.set_group_members(
                        group_id=team.canvas_group_id,
                        user_ids=canvas_user_ids
                    ))

                    # Update last sync timestamp
                    team.last_synced_at = timezone.now()
                    team.save()
                except Exception as e:
                    logger.error(f"Error updating Canvas group members: {e}")

            # Start thread
            update_thread = threading.Thread(target=update_canvas_group)
            update_thread.daemon = True
            update_thread.start()

        # Remove the student from the team
        student.team = None
        student.save()

        return JsonResponse({
            'status': 'success',
            'student': {
                'id': student.id,
                'name': student.full_name,
                'email': student.email
            },
            'old_team': old_team
        })
    except Student.DoesNotExist:
        return JsonResponse({'error': 'Student not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Failed to remove student from team: {str(e)}'}, status=500)


@csrf_exempt
@require_POST
@login_required
def create_canvas_group_category(request, course_id):
    """
    Create a new group category in Canvas.
    Expects a POST with JSON: { "name": "Category Name", "self_signup": "restricted" }
    """
    import json
    course = get_object_or_404(CanvasCourse, canvas_id=course_id)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        return JsonResponse({'error': 'You do not have access to this course'}, status=403)

    try:
        data = json.loads(request.body)
        name = data.get('name', '').strip()
        self_signup = data.get('self_signup', 'restricted')

        if not name:
            return JsonResponse({'error': 'Category name is required'}, status=400)

    except Exception as e:
        return JsonResponse({'error': f'Invalid request format: {str(e)}'}, status=400)

    # Create the category in Canvas
    client = Client(integration)
    import asyncio

    try:
        result = asyncio.run(client.create_group_category(
            course_id=course_id,
            name=name,
            self_signup=self_signup
        ))

        if not result or 'id' not in result:
            return JsonResponse({'error': 'Failed to create group category in Canvas'}, status=500)

        return JsonResponse({
            'status': 'success',
            'category': {
                'id': result['id'],
                'name': result['name'],
                'self_signup': result.get('self_signup', 'restricted')
            }
        })
    except Exception as e:
        return JsonResponse({'error': f'Failed to create group category: {str(e)}'}, status=500)


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
        syncer = CanvasSyncer(client)
        try:
            asyncio.run(sync_courses(syncer, course_ids, user_id))
        except Exception as e:
            # Handle any unexpected errors in the thread
            SyncProgress.complete_sync(user_id, None, success=False, error=str(e))

    async def sync_courses(syncer, course_ids, user_id):
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

                # This will automatically update progress through the syncer
                course = await syncer.sync_course(course_id, user_id)
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
