"""
Views for Canvas synchronization
"""

import logging
import json
import threading
import asyncio
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt

from ..models import CanvasCourse
from ..decorators import canvas_integration_required, canvas_integration_required_json
from ..client import Client
from ..progress import SyncProgress
from ..sync_utils import sync_course_groups

logger = logging.getLogger(__name__)


@canvas_integration_required
def canvas_sync(request):
    """Sync all courses from Canvas"""
    integration = request.canvas_integration

    # For a direct URL access, we'll redirect to a page that shows progress
    # Initialize the sync in a background thread
    user_id = request.user.id

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


@canvas_integration_required
def canvas_sync_single_course(request, course_id):
    """Sync a single course from Canvas"""
    integration = request.canvas_integration

    # Initialize the sync in a background thread
    user_id = request.user.id

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


@canvas_integration_required
def canvas_sync_progress(request):
    """
    Get the current progress of a sync operation
    """
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


@canvas_integration_required
def canvas_sync_batch_progress(request):
    """
    Get the current progress of a batch sync operation
    """
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

    # Debug and ensure course names are properly set in each status
    if "course_statuses" in progress:
        # Ensure each course status has a properly formatted name
        for course_id, status in progress["course_statuses"].items():
            # If the name is missing or is just "Course ID", try to get from DB
            if "name" not in status or status["name"].startswith("Course "):
                try:
                    from lms.canvas.models import CanvasCourse
                    course = CanvasCourse.objects.filter(
                        canvas_id=course_id).first()
                    if course:
                        # If we have the course in the DB, use its name
                        course_name = course.name
                        course_code = course.course_code

                        # Check if name and course_code are the same or if name already contains course_code
                        if course_code and course_name != course_code and course_name not in course_code:
                            status["name"] = f"{course_code}: {course_name}"
                        else:
                            status["name"] = course_name
                except Exception as e:
                    # Just log, don't block the response
                    logger.error(f"Error fetching course name for status: {e}")

    return JsonResponse(progress)


@csrf_exempt
@require_POST
@canvas_integration_required_json
def canvas_sync_selected_courses(request):
    """
    Sync only the selected Canvas courses. Expects a POST with JSON: { "course_ids": [123, 456, ...] }
    Uses AJAX with progress tracking for better UX.
    """
    integration = request.canvas_integration

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
                        headers={
                            "Authorization": f"Bearer {integration.api_key}"}
                    ).json()

                    if "name" in course_data:
                        # Store the name without duplication
                        course_name = course_data["name"]
                        course_code = course_data.get("course_code", "")

                        # Check if name and course_code are the same or if name already contains course_code
                        if course_code and course_name != course_code and course_name not in course_code:
                            course_names[str(course_id)
                                         ] = f"{course_code}: {course_name}"
                        else:
                            course_names[str(course_id)] = course_name
                except Exception as e:
                    logger.error(
                        f"Error fetching course name for {course_id}: {e}")
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
    batch_info = SyncProgress.start_batch_sync(
        user_id, course_ids, course_names)
    batch_id = batch_info["batch_id"]

    # Add a session flag to indicate batch sync is in progress
    request.session[f"canvas_sync_batch_{batch_id}_in_progress"] = True

    def run_sync():
        client = Client(integration)
        try:
            asyncio.run(sync_courses(client, course_ids,
                        user_id, batch_id, course_names))
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
                course_statuses[course_id_str]["started_at"] = timezone.now(
                ).isoformat()

                # Update batch progress just for this course
                await SyncProgress.async_update_batch(
                    user_id,
                    batch_id,
                    course_statuses,
                    current=len([s for s in course_statuses.values() if s.get(
                        "status") == SyncProgress.STATUS_SUCCESS]),
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
                course_statuses[course_id_str]["completed_at"] = timezone.now(
                ).isoformat()

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
                course_statuses[course_id_str]["completed_at"] = timezone.now(
                ).isoformat()

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
            current_tasks = [sync_course_task(
                course_id, idx) for idx, course_id in enumerate(batch)]

            # Wait for all tasks in this batch to complete
            results = await asyncio.gather(*current_tasks, return_exceptions=False)

            # Process results
            for result in results:
                if result.get("success", False):
                    synced.append(result["course_id"])
                else:
                    errors.append({"course_id": result["course_id"], "error": result.get(
                        "error", "Unknown error")})

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


@canvas_integration_required
def canvas_sync_course_groups(request, course_id):
    """
    Sync only the groups and group memberships for a course.
    This is more efficient than syncing the entire course when only group data is needed.
    """
    integration = request.canvas_integration

    # Initialize the sync in a background thread
    user_id = request.user.id

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
