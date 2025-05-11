"""
Utility functions for Canvas data synchronization.
"""

import logging
from typing import List, Dict, Optional, Any

from lms.canvas.client import Client
from lms.canvas.models import CanvasCourse, CanvasIntegration
from lms.canvas.progress import SyncProgress

logger = logging.getLogger(__name__)


async def sync_selected_courses(
    integration: CanvasIntegration, course_ids: List[int], user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Sync selected Canvas courses.

    Args:
        integration: The Canvas integration to use
        course_ids: List of Canvas course IDs to sync
        user_id: Optional user ID for progress tracking

    Returns:
        Dictionary with sync results
    """
    client = Client(integration)
    synced = []
    errors = []

    # Initialize progress tracking if user_id is provided
    if user_id:
        await SyncProgress.async_start_sync(user_id, None, total_steps=len(course_ids))

    for i, course_id in enumerate(course_ids):
        try:
            # Update progress
            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    None,
                    current=i,
                    total=len(course_ids),
                    status="syncing_course",
                    message=f"Syncing course {i+1} of {len(course_ids)}",
                )

            # Sync the course
            course = await client.sync_course(course_id, user_id)
            synced.append(course_id)

            # Log success
            logger.info(f"Successfully synced course: {course.name} (ID: {course_id})")

        except Exception as e:
            # Log error and continue with next course
            logger.error(f"Error syncing course {course_id}: {e}")
            errors.append({"course_id": course_id, "error": str(e)})

    # Finalize progress
    if user_id:
        success = len(synced) > 0
        message = f"Completed sync of {len(synced)} out of {len(course_ids)} courses."
        error = None if success else "Failed to sync any courses"

        await SyncProgress.async_complete_sync(
            user_id, None, success=success, message=message, error=error
        )

    return {
        "synced": synced,
        "errors": errors,
        "total": len(course_ids),
        "success_count": len(synced),
    }


async def sync_course_groups(
    integration: CanvasIntegration, course_id: int, user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Sync Canvas groups for a specific course.

    Args:
        integration: The Canvas integration to use
        course_id: Canvas course ID to sync groups for
        user_id: Optional user ID for progress tracking

    Returns:
        Dictionary with sync results
    """
    client = Client(integration)
    from lms.canvas.syncer import CanvasSyncer

    try:
        # First get or fetch the course
        try:
            course = await CanvasCourse.objects.aget(
                canvas_id=course_id, integration=integration
            )
        except CanvasCourse.DoesNotExist:
            # Course not in database, fetch and sync basic info first
            course = await client.sync_course(course_id, user_id)

        # Create syncer and sync groups
        syncer = CanvasSyncer(client)
        group_ids = await syncer.sync_canvas_groups(course, user_id)

        # Sync group memberships
        await syncer.sync_group_memberships(course, user_id)

        return {
            "course": course,
            "group_count": len(group_ids),
            "group_ids": group_ids,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Error syncing groups for course {course_id}: {e}")
        if user_id:
            await SyncProgress.async_complete_sync(
                user_id,
                course_id,
                success=False,
                message=f"Failed to sync groups for course {course_id}",
                error=str(e),
            )

        return {"course_id": course_id, "success": False, "error": str(e)}


async def push_team_assignments_to_canvas(
    integration: CanvasIntegration, course_id: int, user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Push team assignments from local database to Canvas.

    Args:
        integration: The Canvas integration to use
        course_id: Canvas course ID to push team assignments for
        user_id: Optional user ID for progress tracking

    Returns:
        Dictionary with sync results
    """
    client = Client(integration)
    from lms.canvas.syncer import CanvasSyncer

    try:
        # First get the course
        course = await CanvasCourse.objects.aget(
            canvas_id=course_id, integration=integration
        )

        # Create syncer and push assignments
        syncer = CanvasSyncer(client)
        await syncer.push_group_assignments(course)

        return {
            "course": course,
            "success": True,
            "message": f"Successfully pushed team assignments for {course.name}",
        }

    except Exception as e:
        logger.error(f"Error pushing team assignments for course {course_id}: {e}")
        return {"course_id": course_id, "success": False, "error": str(e)}


async def sync_course_groups(
    integration: CanvasIntegration, course_id: int, user_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Sync only the groups and group memberships for a Canvas course.
    This is more efficient than syncing an entire course when only group data is needed.

    Args:
        integration: The Canvas integration to use
        course_id: Canvas course ID to sync groups for
        user_id: Optional user ID for progress tracking

    Returns:
        Dictionary with sync results
    """
    client = Client(integration)
    from lms.canvas.syncer import CanvasSyncer

    try:
        # Update progress if tracking
        if user_id:
            await SyncProgress.async_update(
                user_id,
                course_id,
                current=1,
                total=5,
                status="fetching_course",
                message="Getting course information..."
            )

        # First, get the course
        try:
            course = await CanvasCourse.objects.aget(
                canvas_id=course_id, integration=integration
            )
        except CanvasCourse.DoesNotExist:
            # Course not in database, fetch basic info first
            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    course_id,
                    current=2,
                    total=5,
                    status="fetching_course_api",
                    message="Fetching course from Canvas API..."
                )
            course_data = await client.get_course(course_id)
            course = await client._save_course(course_data)

        # Update progress
        if user_id:
            await SyncProgress.async_update(
                user_id,
                course_id,
                current=2,
                total=5,
                status="fetching_groups",
                message="Fetching group categories and groups..."
            )

        # Create syncer instance
        syncer = CanvasSyncer(client)

        # Fetch and process group categories and groups
        group_ids = await syncer.sync_canvas_groups(course, user_id)

        # Update progress
        if user_id:
            await SyncProgress.async_update(
                user_id,
                course_id,
                current=3,
                total=5,
                status="syncing_members",
                message="Syncing group memberships..."
            )

        # Sync group memberships
        await syncer.sync_group_memberships(course, user_id)

        # Update progress
        if user_id:
            await SyncProgress.async_update(
                user_id,
                course_id,
                current=4,
                total=5,
                status="updating_timestamp",
                message="Updating timestamps..."
            )

        # Force an update to the course's updated_at timestamp
        # The updated_at field has auto_now=True so it will update automatically
        await course.asave()

        return {
            "course": course,
            "group_count": len(group_ids),
            "group_ids": group_ids,
            "success": True,
        }

    except Exception as e:
        logger.error(f"Error syncing groups for course {course_id}: {e}")

        if user_id:
            await SyncProgress.async_complete_sync(
                user_id,
                course_id,
                success=False,
                message=f"Failed to sync groups for course {course_id}",
                error=str(e),
            )

        return {"course_id": course_id, "success": False, "error": str(e)}
