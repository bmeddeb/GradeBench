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
from django.utils import timezone
import httpx
import requests
from datetime import datetime

from .models import (
    CanvasIntegration,
    CanvasCourse,
    CanvasEnrollment,
    CanvasAssignment,
    CanvasSubmission,
    CanvasGroupCategory,
    CanvasGroup,
    CanvasGroupMembership,
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
        return redirect("login")

    integration = get_integration_for_user(request.user)

    if not integration:
        return redirect("canvas_setup")

    # Get all enrollments that are students from all courses
    enrollments = CanvasEnrollment.objects.filter(
        course__integration=integration, role="StudentEnrollment"
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
            }
        students_by_id[enrollment.user_id]["courses"].append(
            {"course": enrollment.course, "enrollment": enrollment}
        )

    context = {
        "integration": integration,
        "students": list(students_by_id.values()),
    }

    return render(request, "canvas/students_list.html", context)


def canvas_assignments_list(request):
    """View listing all Canvas assignments across all courses"""
    if not request.user.is_authenticated:
        return redirect("login")

    integration = get_integration_for_user(request.user)

    if not integration:
        return redirect("canvas_setup")

    # Get all assignments from all courses
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

    context = {
        "integration": integration,
        "assignments_by_course": list(assignments_by_course.values()),
    }

    return render(request, "canvas/assignments_list.html", context)


def canvas_courses_list(request):
    """View listing all Canvas courses"""
    if not request.user.is_authenticated:
        return redirect("login")

    integration = get_integration_for_user(request.user)

    if not integration:
        return redirect("canvas_setup")

    # Get courses from database
    courses = list(CanvasCourse.objects.filter(integration=integration))

    # For each course, fetch enrollment and assignment counts
    course_data = []
    for course in courses:
        enrollment_count = CanvasEnrollment.objects.filter(
            course=course, role="StudentEnrollment"
        ).count()
        assignment_count = CanvasAssignment.objects.filter(
            course=course).count()

        course_data.append(
            {
                "course": course,
                "enrollment_count": enrollment_count,
                "assignment_count": assignment_count,
            }
        )

    context = {
        "integration": integration,
        "course_data": course_data,
    }

    return render(request, "canvas/courses_list.html", context)


def canvas_dashboard(request):
    """Dashboard showing Canvas courses and related information"""
    if not request.user.is_authenticated:
        return redirect("login")

    integration = get_integration_for_user(request.user)

    if not integration:
        return redirect("canvas_setup")

    # Get courses from database
    courses = list(CanvasCourse.objects.filter(integration=integration))

    # For each course, fetch enrollment and assignment counts
    course_data = []
    for course in courses:
        enrollment_count = CanvasEnrollment.objects.filter(
            course=course, role="StudentEnrollment"
        ).count()
        assignment_count = CanvasAssignment.objects.filter(
            course=course).count()

        course_data.append(
            {
                "course": course,
                "enrollment_count": enrollment_count,
                "assignment_count": assignment_count,
            }
        )

    context = {
        "integration": integration,
        "course_data": course_data,
    }

    return render(request, "canvas/dashboard.html", context)


def canvas_setup(request):
    """Set up Canvas API integration"""
    if not request.user.is_authenticated:
        return redirect("login")

    integration = get_integration_for_user(request.user)

    if request.method == "POST":
        api_key = request.POST.get("api_key")
        canvas_url = request.POST.get(
            "canvas_url", "https://canvas.instructure.com")

        if not api_key:
            messages.error(request, "API Key is required")
            return render(request, "canvas/setup.html", {"integration": integration})

        # Create or update the integration
        if integration:
            integration.api_key = api_key
            integration.canvas_url = canvas_url
            integration.save()
        else:
            integration = CanvasIntegration(
                user=request.user, api_key=api_key, canvas_url=canvas_url
            )
            integration.save()

        messages.success(request, "Canvas integration set up successfully")
        return redirect("canvas_dashboard")

    return render(request, "canvas/setup.html", {"integration": integration})


def canvas_sync(request):
    """Sync courses from Canvas"""
    if not request.user.is_authenticated:
        return redirect("login")

    integration = get_integration_for_user(request.user)

    if not integration:
        messages.error(request, "Canvas integration not set up")
        return redirect("canvas_setup")

    # For a direct URL access, we'll redirect to a page that shows progress
    # Initialize the sync in a background thread
    user_id = request.user.id
    import threading
    from .client import Client
    import asyncio
    from .progress import SyncProgress

    # Initialize progress tracking
    SyncProgress.start_sync(
        user_id, None, total_steps=10
    )  # Placeholder total, will be updated during sync

    def run_sync():
        client = Client(integration)
        try:
            synced_courses = asyncio.run(client.sync_all_courses(user_id))
            logger.info(
                f"Successfully synced {len(synced_courses)} courses from Canvas"
            )
        except Exception as e:
            logger.exception("Error syncing courses from Canvas")
            # Update progress with error
            SyncProgress.complete_sync(
                user_id,
                None,
                success=False,
                message="Sync failed with an error",
                error=str(e),
            )

    # Start the sync in a background thread
    sync_thread = threading.Thread(target=run_sync)
    sync_thread.daemon = True
    sync_thread.start()

    # Redirect to dashboard with message that sync has started
    messages.info(
        request,
        "Syncing courses from Canvas. This may take a while. You can check progress below.",
    )

    # Add a session flag to indicate sync is in progress
    request.session["canvas_sync_in_progress"] = True
    request.session["canvas_sync_started"] = True

    return redirect("canvas_dashboard")


def course_detail(request, course_id):
    """View a single Canvas course with enrollments and assignments"""
    if not request.user.is_authenticated:
        return redirect("login")

    course = get_object_or_404(CanvasCourse, canvas_id=course_id)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        messages.error(request, "You do not have access to this course")
        return redirect("canvas_dashboard")

    # Get enrollments and assignments
    enrollments = list(
        CanvasEnrollment.objects.filter(
            course=course).order_by("role", "sortable_name")
    )

    assignments = list(
        CanvasAssignment.objects.filter(
            course=course).order_by("position", "due_at")
    )

    # Get some statistics
    student_count = len(
        [e for e in enrollments if e.role == "StudentEnrollment"])
    instructor_count = len(
        [e for e in enrollments if e.role in ["TeacherEnrollment", "TaEnrollment"]]
    )

    context = {
        "course": course,
        "enrollments": enrollments,
        "assignments": assignments,
        "student_count": student_count,
        "instructor_count": instructor_count,
    }

    return render(request, "canvas/course_detail.html", context)


def assignment_detail(request, course_id, assignment_id):
    """View a single assignment with submissions"""
    if not request.user.is_authenticated:
        return redirect("login")

    course = get_object_or_404(CanvasCourse, canvas_id=course_id)
    assignment = get_object_or_404(
        CanvasAssignment, canvas_id=assignment_id, course=course
    )

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        messages.error(request, "You do not have access to this course")
        return redirect("canvas_dashboard")

    # Get all submissions for this assignment
    submissions = list(
        CanvasSubmission.objects.filter(assignment=assignment).select_related(
            "enrollment"
        )  # Pre-fetch related enrollments
    )

    # Get statistics
    submitted_count = len(
        [s for s in submissions if s.workflow_state == "submitted"])
    graded_count = len(
        [s for s in submissions if s.workflow_state == "graded"])
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
                                "canvas_id", flat=True)
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
    except:
        pass

    context = {
        "course": course,
        "assignment": assignment,
        "submissions": submissions,
        "submitted_count": submitted_count,
        "graded_count": graded_count,
        "missing_count": missing_count,
        "late_count": late_count,
        "has_rubric": has_rubric,
        "rubric": rubric,
    }

    return render(request, "canvas/assignment_detail.html", context)


def student_detail(request, course_id, user_id):
    """View a single student's information and submissions"""
    if not request.user.is_authenticated:
        return redirect("login")

    course = get_object_or_404(CanvasCourse, canvas_id=course_id)
    enrollment = get_object_or_404(
        CanvasEnrollment, course=course, user_id=user_id)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        messages.error(request, "You do not have access to this course")
        return redirect("canvas_dashboard")

    # Get all submissions for this student in this course
    submissions = list(
        CanvasSubmission.objects.filter(enrollment=enrollment).select_related(
            "assignment"
        )  # Pre-fetch related assignments
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

    context = {
        "course": course,
        "enrollment": enrollment,
        "submissions": submissions,
        "assignment_count": assignment_count,
        "submitted_count": submitted_count,
        "missing_count": missing_count,
        "late_count": late_count,
        "current_score": current_score,
        "final_score": final_score,
    }

    return render(request, "canvas/student_detail.html", context)


def canvas_delete_course(request, course_id):
    """Delete a Canvas course and all related data"""
    if not request.user.is_authenticated:
        return redirect("login")

    integration = get_integration_for_user(request.user)
    if not integration:
        return redirect("canvas_setup")

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


def canvas_sync_single_course(request, course_id):
    """Sync a single course from Canvas"""
    if not request.user.is_authenticated:
        return redirect("login")

    integration = get_integration_for_user(request.user)

    if not integration:
        messages.error(request, "Canvas integration not set up")
        return redirect("canvas_setup")

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
                error=str(e),
            )

    # Start the sync in a background thread
    sync_thread = threading.Thread(target=run_sync)
    sync_thread.daemon = True
    sync_thread.start()

    # Redirect with message that sync has started
    messages.info(
        request,
        "Course sync has started. This may take a while. You can check progress below.",
    )

    # Add a session flag to indicate sync is in progress
    request.session[f"canvas_sync_course_{course_id}_in_progress"] = True

    return redirect("canvas_course_detail", course_id=course_id)


@login_required
def canvas_list_available_courses(request):
    """
    Fetches the list of available Canvas courses for the authenticated user (preview only).
    """
    integration = get_integration_for_user(request.user)
    if not integration:
        return JsonResponse({"error": "Canvas integration not set up"}, status=400)

    api_url = (
        integration.canvas_url.rstrip("/")
        + "/api/v1/courses?per_page=100&enrollment_state=active"
    )
    headers = {
        "Authorization": f"Bearer {integration.api_key}",
    }
    all_courses = []
    url = api_url

    while url:
        resp = httpx.get(url, headers=headers)
        if resp.status_code != 200:
            return JsonResponse(
                {"error": "Failed to fetch courses from Canvas"},
                status=resp.status_code,
            )
        courses = resp.json()
        all_courses.extend(courses)
        # Handle pagination
        link = resp.headers.get("Link")
        next_url = None
        if link:
            for part in link.split(","):
                if 'rel="next"' in part:
                    next_url = part.split(";")[0].strip()[1:-1]
                    break
        url = next_url

    course_list = [
        {
            "id": c["id"],
            "name": c["name"],
            "course_code": c.get("course_code", ""),
            "start_at": c.get("start_at", ""),
            "end_at": c.get("end_at", ""),
            "workflow_state": c.get("workflow_state", ""),
        }
        for c in all_courses
    ]
    return JsonResponse({"courses": course_list})


@login_required
def canvas_sync_progress(request):
    """
    Get the current progress of a sync operation
    """
    from .progress import SyncProgress

    user_id = request.user.id
    course_id = request.GET.get("course_id")

    progress = SyncProgress.get(user_id, course_id)

    # If the status is completed or error, clear any session flags
    if course_id and progress.get("status") in [
        SyncProgress.STATUS_COMPLETED,
        SyncProgress.STATUS_ERROR,
    ]:
        session_key = f"canvas_sync_course_{course_id}_in_progress"
        if session_key in request.session:
            del request.session[session_key]
    elif not course_id and progress.get("status") in [
        SyncProgress.STATUS_COMPLETED,
        SyncProgress.STATUS_ERROR,
    ]:
        if "canvas_sync_in_progress" in request.session:
            del request.session["canvas_sync_in_progress"]

    return JsonResponse(progress)


@login_required
def canvas_sync_batch_progress(request):
    """
    Get the current progress of a batch sync operation
    """
    from .progress import SyncProgress

    user_id = request.user.id
    batch_id = request.GET.get("batch_id")

    if not batch_id:
        return JsonResponse({"error": "Batch ID is required"}, status=400)

    progress = SyncProgress.get_batch_progress(user_id, batch_id)

    # If the status is completed or error, clear any session flags
    if progress.get("status") in [
        SyncProgress.STATUS_COMPLETED,
        SyncProgress.STATUS_ERROR,
    ]:
        session_key = f"canvas_sync_batch_{batch_id}_in_progress"
        if session_key in request.session:
            del request.session[session_key]

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
        return JsonResponse({"error": "Canvas integration not set up"}, status=400)

    try:
        data = json.loads(request.body)
        course_ids = data.get("course_ids", [])
        if not course_ids:
            return JsonResponse(
                {
                    "error": "Please select at least one course to sync",
                    "status": "error",
                },
                status=400,
            )
    except Exception as e:
        return JsonResponse(
            {"error": f"Invalid request format: {str(e)}", "status": "error"},
            status=400,
        )

    # For AJAX, we're going to start the sync process asynchronously and
    # immediately return a response to the client indicating that the
    # sync has been started
    user_id = request.user.id

    # Start the sync in a background thread
    import threading
    from .client import Client
    import asyncio
    from .progress import SyncProgress

    # Fetch course names for better display
    course_names = {}
    
    def fetch_course_names():
        try:
            client = Client(integration)
            for course_id in course_ids:
                try:
                    # Use a synchronous approach for simplicity
                    course_data = requests.get(
                        f"{integration.canvas_url.rstrip('/')}/api/v1/courses/{course_id}",
                        headers={"Authorization": f"Bearer {integration.api_key}"}
                    ).json()
                    
                    if "name" in course_data:
                        course_names[str(course_id)] = course_data["name"]
                except Exception as e:
                    logger.error(f"Error fetching course name for {course_id}: {e}")
                    # Use a default name if we can't fetch the real one
                    course_names[str(course_id)] = f"Course {course_id}"
        except Exception as e:
            logger.error(f"Error fetching course names: {e}")
    
    # Fetch course names in a separate thread to avoid delaying the response
    name_thread = threading.Thread(target=fetch_course_names)
    name_thread.daemon = True
    name_thread.start()
    
    # Wait a very short time for names to be fetched
    name_thread.join(timeout=0.5)
    
    # Initialize batch progress tracking
    batch_info = SyncProgress.start_batch_sync(user_id, course_ids, course_names)
    batch_id = batch_info["batch_id"]
    
    # Add a session flag to indicate batch sync is in progress
    request.session[f"canvas_sync_batch_{batch_id}_in_progress"] = True

    def run_sync():
        client = Client(integration)
        try:
            asyncio.run(sync_courses(client, course_ids, user_id, batch_id, course_names))
        except Exception as e:
            # Log full exception for debugging
            logger.exception("Error syncing selected courses")
            # Handle any unexpected errors in the thread
            SyncProgress.complete_batch_sync(
                user_id, batch_id, success=False, error=str(e))
            SyncProgress.complete_sync(
                user_id, None, success=False, error=str(e))

    async def sync_courses(client, course_ids, user_id, batch_id, course_names):
        synced = []
        errors = []
        
        # Get course statuses from the current batch progress
        batch_progress = await SyncProgress.async_get_batch_progress(user_id, batch_id)
        course_statuses = batch_progress.get("course_statuses", {})
        
        # If course_statuses is empty (shouldn't happen but just in case)
        if not course_statuses:
            course_statuses = {
                str(course_id): {
                    "name": course_names.get(str(course_id), f"Course {course_id}"),
                    "status": SyncProgress.STATUS_QUEUED,
                    "progress": 0,
                    "message": "Waiting to start",
                    "started_at": None,
                    "completed_at": None
                } for course_id in course_ids
            }
            
        # Update all courses to "Queued" status
        for course_id in course_ids:
            course_id_str = str(course_id)
            course_statuses[course_id_str]["status"] = SyncProgress.STATUS_QUEUED
            course_statuses[course_id_str]["message"] = "Queued for sync"
            course_statuses[course_id_str]["progress"] = 0
        
        # Update batch progress with all courses queued
        await SyncProgress.async_update_batch(
            user_id,
            batch_id,
            course_statuses,
            current=0,
            total=len(course_ids),
            status=SyncProgress.STATUS_IN_PROGRESS,
            message=f"Starting sync of {len(course_ids)} courses"
        )
        
        # Also update standard progress for compatibility
        await SyncProgress.async_update(
            user_id,
            None,
            current=0,
            total=len(course_ids),
            status="syncing_course",
            message=f"Starting sync of {len(course_ids)} courses"
        )
        
        # Define a task for each course
        async def sync_course_task(course_id, i):
            course_id_str = str(course_id)
            try:
                # Mark this course as in progress
                course_statuses[course_id_str]["status"] = SyncProgress.STATUS_IN_PROGRESS
                course_statuses[course_id_str]["message"] = "Starting sync"
                course_statuses[course_id_str]["progress"] = 0
                course_statuses[course_id_str]["started_at"] = timezone.now().isoformat()
                
                # Update batch progress just for this course
                await SyncProgress.async_update_batch(
                    user_id,
                    batch_id,
                    course_statuses,
                    current=len([s for s in course_statuses.values() if s.get("status") == SyncProgress.STATUS_SUCCESS]),
                    total=len(course_ids),
                    status=SyncProgress.STATUS_IN_PROGRESS,
                    message=f"Processing {len(course_ids)} courses concurrently"
                )
                
                # Create a progress callback for this course
                async def update_course_progress(status, message, progress):
                    # Update this course's status in the batch
                    course_statuses[course_id_str]["status"] = SyncProgress.STATUS_IN_PROGRESS
                    course_statuses[course_id_str]["message"] = message
                    course_statuses[course_id_str]["progress"] = int(progress)
                    
                    # Update the batch progress - count completed courses
                    completed_count = len([s for s in course_statuses.values() 
                                          if s.get("status") in [SyncProgress.STATUS_SUCCESS, SyncProgress.STATUS_ERROR]])
                    
                    await SyncProgress.async_update_batch(
                        user_id,
                        batch_id,
                        course_statuses,
                        current=completed_count,
                        total=len(course_ids),
                        status=SyncProgress.STATUS_IN_PROGRESS,
                        message=f"Processing {len(course_ids)} courses concurrently"
                    )
                
                # This will automatically update progress through the callback
                course = await client.sync_course(course_id, None, update_course_progress)
                
                # Mark course as completed in batch
                course_statuses[course_id_str]["status"] = SyncProgress.STATUS_SUCCESS
                course_statuses[course_id_str]["message"] = "Sync completed successfully"
                course_statuses[course_id_str]["progress"] = 100
                course_statuses[course_id_str]["completed_at"] = timezone.now().isoformat()
                
                # Count completed courses for the overall progress
                completed_count = len([s for s in course_statuses.values() 
                                      if s.get("status") in [SyncProgress.STATUS_SUCCESS, SyncProgress.STATUS_ERROR]])
                
                # Update batch progress
                await SyncProgress.async_update_batch(
                    user_id,
                    batch_id,
                    course_statuses,
                    current=completed_count,
                    total=len(course_ids),
                    status=SyncProgress.STATUS_IN_PROGRESS,
                    message=f"Completed {completed_count} of {len(course_ids)} courses"
                )
                
                return {"course_id": course_id, "success": True, "course": course}
            except Exception as e:
                logger.error(f"Error syncing course {course_id}: {e}")
                
                # Mark course as failed in batch
                course_statuses[course_id_str]["status"] = SyncProgress.STATUS_ERROR
                course_statuses[course_id_str]["message"] = f"Error: {str(e)}"
                course_statuses[course_id_str]["completed_at"] = timezone.now().isoformat()
                
                # Count completed courses (including errors) for the overall progress
                completed_count = len([s for s in course_statuses.values() 
                                      if s.get("status") in [SyncProgress.STATUS_SUCCESS, SyncProgress.STATUS_ERROR]])
                
                # Update batch progress
                await SyncProgress.async_update_batch(
                    user_id,
                    batch_id,
                    course_statuses,
                    current=completed_count,
                    total=len(course_ids),
                    status=SyncProgress.STATUS_IN_PROGRESS,
                    message=f"Completed {completed_count} of {len(course_ids)} courses"
                )
                
                return {"course_id": course_id, "success": False, "error": str(e)}
        
        # Create task list with a max concurrency of 5 courses at a time
        # This helps prevent overwhelming the Canvas API or the server
        MAX_CONCURRENT = 5
        tasks = []
        
        # Process courses in batches of MAX_CONCURRENT
        for i in range(0, len(course_ids), MAX_CONCURRENT):
            batch = course_ids[i:i+MAX_CONCURRENT]
            current_tasks = [sync_course_task(course_id, idx) for idx, course_id in enumerate(batch)]
            
            # Wait for all tasks in this batch to complete
            results = await asyncio.gather(*current_tasks, return_exceptions=False)
            
            # Process results
            for result in results:
                if result.get("success", False):
                    synced.append(result["course_id"])
                else:
                    errors.append({"course_id": result["course_id"], "error": result.get("error", "Unknown error")})
        
        # Mark the overall sync as complete
        success = len(synced) > 0
        message = f"Completed sync of {len(synced)} out of {len(course_ids)} courses."
        error = None if success else "Failed to sync any courses"

        await SyncProgress.async_complete_batch_sync(
            user_id, batch_id, success=success, message=message, error=error
        )
        
        # Also complete standard progress for compatibility
        await SyncProgress.async_complete_sync(
            user_id, None, success=success, message=message, error=error
        )

    # Start the sync in a background thread
    sync_thread = threading.Thread(target=run_sync)
    sync_thread.daemon = True
    sync_thread.start()

    # Return immediately with a response that the sync has been started
    return JsonResponse(
        {
            "status": "started",
            "message": f"Started syncing {len(course_ids)} course(s)",
            "course_ids": course_ids,
            "batch_id": batch_id
        }
    )


@login_required
def course_groups(request, course_id):
    """
    View the groups for a course, organized by group sets (categories).
    This is the main page for the group management module.
    """
    if not request.user.is_authenticated:
        return redirect("login")

    course = get_object_or_404(CanvasCourse, canvas_id=course_id)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        messages.error(request, "You do not have access to this course")
        return redirect("canvas_dashboard")

    # Get all group categories (sets) for this course
    group_categories = CanvasGroupCategory.objects.filter(
        course=course).order_by("name")

    # Get all groups for each category to display counts
    category_data = []
    for category in group_categories:
        groups_count = CanvasGroup.objects.filter(category=category).count()

        # Count members across all groups in this category
        memberships_count = CanvasGroupMembership.objects.filter(
            group__category=category
        ).count()

        category_data.append({
            "category": category,
            "groups_count": groups_count,
            "members_count": memberships_count,
        })

    # Get all student enrollments for this course
    enrollments = CanvasEnrollment.objects.filter(
        course=course, role="StudentEnrollment"
    ).order_by("sortable_name")

    # Get total number of students and unassigned students count
    total_students = enrollments.count()

    # Find students who have group memberships
    students_with_groups = CanvasGroupMembership.objects.filter(
        group__category__course=course
    ).values_list("user_id", flat=True).distinct()

    # Count students without group memberships
    unassigned_students = CanvasEnrollment.objects.filter(
        course=course,
        role="StudentEnrollment"
    ).exclude(
        user_id__in=students_with_groups
    ).count()

    # Pass first category as default selected if exists
    default_category = None
    if category_data:
        default_category = category_data[0]["category"]

    # Sync status info
    last_sync = course.updated_at if hasattr(course, "updated_at") else None

    context = {
        "course": course,
        "category_data": category_data,
        "total_students": total_students,
        "unassigned_students": unassigned_students,
        "last_sync": last_sync,
        "default_category": default_category,
    }

    return render(request, "canvas/groups/index.html", context)


@login_required
def group_set_detail(request, course_id, group_set_id):
    """
    AJAX endpoint to get detailed information about a specific group set,
    including all groups and their members.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    course = get_object_or_404(CanvasCourse, canvas_id=course_id)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        return JsonResponse({"error": "Access denied"}, status=403)

    # Get the group category (set)
    try:
        category = get_object_or_404(
            CanvasGroupCategory, id=group_set_id, course=course)
    except CanvasGroupCategory.DoesNotExist:
        return JsonResponse({"error": "Group set not found"}, status=404)

    # Get all groups in this category
    groups = CanvasGroup.objects.filter(category=category).order_by("name")

    # Build response with groups and their members
    group_data = []
    for group in groups:
        # Get members for this group
        memberships = CanvasGroupMembership.objects.filter(group=group)

        # Get the associated core team if it exists
        core_team = None
        if hasattr(group, "core_team") and group.core_team:
            core_team = {
                "id": group.core_team.id,
                "name": group.core_team.name,
            }

        # Add to response
        group_data.append({
            "id": group.id,
            "canvas_id": group.canvas_id,
            "name": group.name,
            "description": group.description,
            "created_at": group.created_at.isoformat() if group.created_at else None,
            "members": [
                {
                    "id": membership.id,
                    "user_id": membership.user_id,
                    "name": membership.name,
                    "email": membership.email,
                    "student_id": membership.student_id if hasattr(membership, "student") else None,
                }
                for membership in memberships
            ],
            "core_team": core_team,
        })

    # Get unassigned students (those without a group in this category)
    assigned_student_ids = CanvasGroupMembership.objects.filter(
        group__category=category
    ).values_list("user_id", flat=True)

    unassigned_students = CanvasEnrollment.objects.filter(
        course=course,
        role="StudentEnrollment"
    ).exclude(
        user_id__in=assigned_student_ids
    ).values("user_id", "user_name", "email")

    # Build response
    response_data = {
        "category": {
            "id": category.id,
            "canvas_id": category.canvas_id,
            "name": category.name,
            "self_signup": category.self_signup,
            "group_limit": category.group_limit,
            "auto_leader": category.auto_leader,
            "created_at": category.created_at.isoformat() if category.created_at else None,
        },
        "groups": group_data,
        "unassigned_students": list(unassigned_students),
    }

    return JsonResponse(response_data)


@login_required
def canvas_sync_course_groups(request, course_id):
    """
    Sync only the groups and group memberships for a course.
    This is more efficient than syncing the entire course when only group data is needed.
    """
    if not request.user.is_authenticated:
        return redirect("login")

    integration = get_integration_for_user(request.user)
    if not integration:
        messages.error(request, "Canvas integration not set up")
        return redirect("canvas_setup")

    # Initialize the sync in a background thread
    user_id = request.user.id
    import threading
    import asyncio
    from .progress import SyncProgress
    from .sync_utils import sync_course_groups

    # Initialize progress tracking before starting the thread
    SyncProgress.start_sync(user_id, course_id, total_steps=5)
    SyncProgress.update(
        user_id,
        course_id,
        current=1,
        total=5,
        status="starting",
        message="Starting group sync..."
    )

    def run_sync():
        try:
            # Use the targeted sync function from sync_utils
            result = asyncio.run(sync_course_groups(
                integration, course_id, user_id))

            if result.get("success", False):
                # Update progress with success
                SyncProgress.complete_sync(
                    user_id,
                    course_id,
                    success=True,
                    message=f"Successfully synced groups for course {course_id}",
                )
            else:
                # Update progress with error
                SyncProgress.complete_sync(
                    user_id,
                    course_id,
                    success=False,
                    message="Failed to sync groups",
                    error=result.get("error", "Unknown error"),
                )
        except Exception as e:
            logger.error(f"Error syncing groups for course {course_id}: {e}")
            # Update progress with error
            SyncProgress.complete_sync(
                user_id,
                course_id,
                success=False,
                message="Group sync failed with an error.",
                error=str(e),
            )

    # Start the sync in a background thread
    sync_thread = threading.Thread(target=run_sync)
    sync_thread.daemon = True
    sync_thread.start()

    # If this is an AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            "status": "started",
            "message": "Group sync has started",
        })

    # Otherwise redirect with message
    messages.info(
        request,
        "Group sync has started. This may take a moment. You can check progress below.",
    )

    # Add a session flag to indicate sync is in progress
    request.session[f"canvas_sync_groups_{course_id}_in_progress"] = True

    return redirect("canvas_course_groups", course_id=course_id)


@login_required
def create_group_set(request, course_id):
    """
    Create a new group set (category) for a course.
    This creates both in the local database and in Canvas.
    """
    if not request.user.is_authenticated:
        return redirect("login")

    # Get the course
    course = get_object_or_404(CanvasCourse, canvas_id=course_id)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        messages.error(request, "You do not have access to this course")
        return redirect("canvas_dashboard")

    if request.method == "POST":
        # Create the group set in Canvas and locally
        name = request.POST.get("name")
        self_signup = request.POST.get("self_signup")
        auto_leader = request.POST.get("auto_leader")
        group_limit = request.POST.get("group_limit")

        if not name:
            messages.error(request, "Group set name is required")
            return render(request, "canvas/groups/create_group_set.html", {
                "course": course,
            })

        # Convert empty string to None for numeric field
        if group_limit == "":
            group_limit = None

        try:
            # Use our new synchronous utility function to create the group category
            from lms.canvas.sync_utils import create_group_category_sync

            category, created = create_group_category_sync(
                integration=integration,
                course_id=course_id,
                name=name,
                self_signup=self_signup,
                auto_leader=auto_leader,
                group_limit=group_limit
            )

            messages.success(
                request, f"Group set '{name}' created successfully")
            return redirect("canvas_course_groups", course_id=course_id)

        except Exception as e:
            messages.error(request, f"Error creating group set: {str(e)}")
            return render(request, "canvas/groups/create_group_set.html", {
                "course": course,
                "error": str(e),
            })

    # GET request - show the form
    return render(request, "canvas/groups/create_group_set.html", {
        "course": course,
    })


@login_required
def edit_group_set(request, course_id, group_set_id):
    """
    Edit a group set (category).
    This updates both the local database and Canvas.
    """
    if not request.user.is_authenticated:
        return redirect("login")

    # Get the course and group set
    course = get_object_or_404(CanvasCourse, canvas_id=course_id)
    group_set = get_object_or_404(
        CanvasGroupCategory, id=group_set_id, course=course)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        messages.error(request, "You do not have access to this course")
        return redirect("canvas_dashboard")

    if request.method == "POST":
        # Update the group set in Canvas and locally
        name = request.POST.get("name")
        self_signup = request.POST.get("self_signup")
        auto_leader = request.POST.get("auto_leader")
        group_limit = request.POST.get("group_limit")

        if not name:
            messages.error(request, "Group set name is required")
            return render(request, "canvas/groups/edit_group_set.html", {
                "course": course,
                "group_set": group_set,
            })

        # Convert empty string to None for numeric field
        if group_limit == "":
            group_limit = None

        try:
            # Use our new synchronous utility function to update the group category
            from lms.canvas.sync_utils import update_group_category_sync

            category, updated = update_group_category_sync(
                integration=integration,
                category_id=group_set.canvas_id,
                name=name,
                self_signup=self_signup,
                auto_leader=auto_leader,
                group_limit=group_limit
            )

            # The category is already updated by update_group_category_sync
            # so we don't need to manually update the group_set as we did before

            messages.success(
                request, f"Group set '{name}' updated successfully")
            return redirect("canvas_course_groups", course_id=course_id)

        except Exception as e:
            messages.error(request, f"Error updating group set: {str(e)}")
            return render(request, "canvas/groups/edit_group_set.html", {
                "course": course,
                "group_set": group_set,
                "error": str(e),
            })

    # GET request - show the form
    return render(request, "canvas/groups/edit_group_set.html", {
        "course": course,
        "group_set": group_set,
    })


@login_required
@require_POST
def delete_group_set(request, course_id, group_set_id):
    """
    Delete a group set (category).
    This deletes from both the local database and Canvas.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    # Get the course and group set
    course = get_object_or_404(CanvasCourse, canvas_id=course_id)
    group_set = get_object_or_404(
        CanvasGroupCategory, id=group_set_id, course=course)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        return JsonResponse({"error": "Access denied"}, status=403)

    try:
        # Use our synchronous utility function to delete the group category
        from lms.canvas.sync_utils import delete_group_category_sync

        # Store the name before deletion
        group_set_name = group_set.name
        canvas_category_id = group_set.canvas_id

        # Delete the group category
        success = delete_group_category_sync(
            integration=integration,
            category_id=canvas_category_id
        )

        return JsonResponse({
            "success": True,
            "message": f"Group set '{group_set_name}' deleted successfully",
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": f"Error deleting group set: {str(e)}",
        }, status=500)


@login_required
def create_group(request, course_id, group_set_id):
    """
    Create a new group within a group set.
    This creates both in the local database and in Canvas.
    """
    if not request.user.is_authenticated:
        return redirect("login")

    # Get the course and group set
    course = get_object_or_404(CanvasCourse, canvas_id=course_id)
    group_set = get_object_or_404(
        CanvasGroupCategory, id=group_set_id, course=course)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        messages.error(request, "You do not have access to this course")
        return redirect("canvas_dashboard")

    if request.method == "POST":
        # Create the group in Canvas and locally
        name = request.POST.get("name")
        description = request.POST.get("description", "")

        if not name:
            messages.error(request, "Group name is required")
            return render(request, "canvas/groups/create_group.html", {
                "course": course,
                "group_set": group_set,
            })

        try:
            # Use our synchronous utility function to create the group
            from lms.canvas.sync_utils import create_group_sync

            group, created = create_group_sync(
                integration=integration,
                category_id=group_set.canvas_id,
                name=name,
                description=description
            )

            messages.success(request, f"Group '{name}' created successfully")
            return redirect("canvas_course_groups", course_id=course_id)

        except Exception as e:
            messages.error(request, f"Error creating group: {str(e)}")
            return render(request, "canvas/groups/create_group.html", {
                "course": course,
                "group_set": group_set,
                "error": str(e),
            })

    # GET request - show the form
    return render(request, "canvas/groups/create_group.html", {
        "course": course,
        "group_set": group_set,
    })


@login_required
def edit_group(request, course_id, group_id):
    """
    Edit a group.
    This updates both the local database and Canvas.
    """
    if not request.user.is_authenticated:
        return redirect("login")

    # Get the course and group
    course = get_object_or_404(CanvasCourse, canvas_id=course_id)
    group = get_object_or_404(CanvasGroup, id=group_id)

    # Verify the group belongs to this course
    if group.category.course != course:
        messages.error(request, "Group does not belong to this course")
        return redirect("canvas_course_groups", course_id=course_id)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        messages.error(request, "You do not have access to this course")
        return redirect("canvas_dashboard")

    if request.method == "POST":
        # Update the group in Canvas and locally
        name = request.POST.get("name")
        description = request.POST.get("description", "")

        if not name:
            messages.error(request, "Group name is required")
            return render(request, "canvas/groups/edit_group.html", {
                "course": course,
                "group": group,
            })

        try:
            # Use our synchronous utility function to update the group
            from lms.canvas.sync_utils import update_group_sync

            updated_group, updated = update_group_sync(
                integration=integration,
                group_id=group.canvas_id,
                name=name,
                description=description
            )

            messages.success(request, f"Group '{name}' updated successfully")
            return redirect("canvas_course_groups", course_id=course_id)

        except Exception as e:
            messages.error(request, f"Error updating group: {str(e)}")
            return render(request, "canvas/groups/edit_group.html", {
                "course": course,
                "group": group,
                "error": str(e),
            })

    # GET request - show the form
    return render(request, "canvas/groups/edit_group.html", {
        "course": course,
        "group": group,
    })


@login_required
@require_POST
def delete_group(request, course_id, group_id):
    """
    Delete a group.
    This deletes from both the local database and Canvas.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Authentication required"}, status=401)

    # Get the course and group
    course = get_object_or_404(CanvasCourse, canvas_id=course_id)
    group = get_object_or_404(CanvasGroup, id=group_id)

    # Verify the group belongs to this course
    if group.category.course != course:
        return JsonResponse({"error": "Group does not belong to this course"}, status=403)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        return JsonResponse({"error": "Access denied"}, status=403)

    try:
        # Use our synchronous utility function to delete the group
        from lms.canvas.sync_utils import delete_group_sync

        # Store the name before deletion
        group_name = group.name
        canvas_group_id = group.canvas_id

        # Delete the group
        success = delete_group_sync(
            integration=integration,
            group_id=canvas_group_id
        )

        return JsonResponse({
            "success": True,
            "message": f"Group '{group_name}' deleted successfully",
        })

    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": f"Error deleting group: {str(e)}",
        }, status=500)


@login_required
def push_course_group_memberships(request, course_id):
    """
    Explicitly push all group memberships for a course to Canvas.
    This ensures that Canvas has the same group memberships as our local database.
    """
    if not request.user.is_authenticated:
        return redirect("login")

    # Get the course
    course = get_object_or_404(CanvasCourse, canvas_id=course_id)

    # Check if user has access to this course
    integration = get_integration_for_user(request.user)
    if course.integration != integration:
        messages.error(request, "You do not have access to this course")
        return redirect("canvas_dashboard")

    if request.method == "POST":
        try:
            # Use our synchronous utility function to push all group memberships
            from lms.canvas.sync_utils import push_all_group_memberships_sync

            # Push all memberships
            stats = push_all_group_memberships_sync(integration, course_id)

            if stats["errors"] > 0:
                messages.warning(
                    request,
                    f"Pushed memberships for {stats['groups_updated']} groups, but encountered {stats['errors']} errors. See logs for details."
                )
            else:
                messages.success(
                    request,
                    f"Successfully pushed memberships for {stats['groups_updated']} groups to Canvas."
                )

            return redirect("canvas_course_groups", course_id=course_id)

        except Exception as e:
            messages.error(
                request, f"Error pushing group memberships: {str(e)}")
            return redirect("canvas_course_groups", course_id=course_id)

    # If it's a GET request, show confirmation page
    return render(
        request,
        "canvas/groups/confirm_push_memberships.html",
        {
            "course": course,
        },
    )
