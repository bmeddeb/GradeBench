"""
Utility functions for Canvas data synchronization.
"""

import logging
from typing import List, Dict, Optional, Any

from lms.canvas.client import Client
from lms.canvas.models import CanvasCourse, CanvasIntegration, CanvasGroupCategory, CanvasGroup
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
            logger.info(
                f"Successfully synced course: {course.name} (ID: {course_id})")

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
        logger.error(
            f"Error pushing team assignments for course {course_id}: {e}")
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
                current=0,
                total=1,  # Will be updated once we know total groups
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
                    current=0,
                    total=1,
                    status="fetching_course_api",
                    message="Fetching course from Canvas API..."
                )
            course_data = await client.get_course(course_id)
            course = await client._save_course(course_data)

        # First, get a count of all groups to properly track progress
        if user_id:
            await SyncProgress.async_update(
                user_id,
                course_id,
                current=0,
                total=1,
                status="counting_groups",
                message="Counting groups to sync..."
            )
        
        # Get all categories to count total groups
        categories = await client.get_group_categories(course_id)
        total_groups = 0
        for cat in categories:
            groups = await client.get_groups(cat["id"])
            total_groups += len(groups)
        
        logger.info(f"Found {total_groups} total groups across {len(categories)} categories")
        
        # Handle case where there are no groups
        if total_groups == 0:
            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    course_id,
                    current=1,
                    total=1,
                    status="completed",
                    message="No groups found to sync"
                )
            return {
                "course": course,
                "group_count": 0,
                "group_ids": [],
                "success": True,
            }
        
        # We'll add 2 extra steps: one for syncing memberships, one for completion
        total_steps = total_groups + 2
        
        # Update progress with actual total
        if user_id:
            await SyncProgress.async_update(
                user_id,
                course_id,
                current=0,
                total=total_steps,
                status="fetching_groups",
                message=f"Starting sync of {total_groups} groups..."
            )

        # Create syncer instance
        syncer = CanvasSyncer(client)

        # Fetch and process group categories and groups with progress tracking
        group_ids = await syncer.sync_canvas_groups(course, user_id, total_steps)

        # Sync group memberships - add this as an extra step
        if user_id:
            await SyncProgress.async_update(
                user_id,
                course_id,
                current=total_groups,
                total=total_steps,
                status="syncing_memberships",
                message="Syncing group memberships..."
            )
        
        await syncer.sync_group_memberships(course, user_id, total_steps)

        # Final update - this is the last step
        if user_id:
            await SyncProgress.async_update(
                user_id,
                course_id,
                current=total_steps - 1,
                total=total_steps,
                status="completing",
                message="Finalizing sync..."
            )

        # Force an update to the course's updated_at timestamp
        await course.asave()
        
        # Mark as truly complete
        if user_id:
            await SyncProgress.async_update(
                user_id,
                course_id,
                current=total_steps,
                total=total_steps,
                status="completed",
                message="Group sync completed successfully"
            )

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


def create_group_category_sync(integration, course_id, name, self_signup=None, auto_leader=None, group_limit=None):
    """
    Create a group category in Canvas using synchronous requests.
    This function is intended for use in views where async/await is problematic.

    Args:
        integration: CanvasIntegration instance
        course_id: Canvas course ID
        name: Name of the group category
        self_signup: Optional - "enabled" or "restricted"
        auto_leader: Optional - "first" or "random"
        group_limit: Optional - Maximum members per group

    Returns:
        tuple: (category, created) - The CanvasGroupCategory instance and whether it was created
    """
    import requests
    from datetime import datetime
    from lms.canvas.models import CanvasGroupCategory, CanvasCourse

    # Prepare the API URL and headers
    api_url = f"{integration.canvas_url}/api/v1/courses/{course_id}/group_categories"
    headers = {
        "Authorization": f"Bearer {integration.api_key}",
        "Content-Type": "application/json",
    }

    # Convert group_limit to int if provided
    if group_limit is not None:
        try:
            group_limit = int(group_limit)
        except (ValueError, TypeError):
            group_limit = None

    # Prepare request data
    request_data = {
        "name": name
    }

    # Only add optional parameters if they have values
    if self_signup:
        request_data["self_signup"] = self_signup

    if auto_leader:
        request_data["auto_leader"] = auto_leader

    if group_limit is not None:
        request_data["group_limit"] = group_limit

    # Make the API request
    response = requests.post(api_url, json=request_data, headers=headers)

    # Check for success
    if response.status_code not in [200, 201]:
        error_msg = f"Canvas API error: {response.status_code} - {response.text}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Parse the response
    canvas_response = response.json()

    # Get the course
    course = CanvasCourse.objects.get(canvas_id=course_id)

    # Create or update the group category in our database
    category, created = CanvasGroupCategory.objects.update_or_create(
        canvas_id=canvas_response["id"],
        defaults={
            "course": course,
            "name": canvas_response.get("name", "Unnamed Category"),
            "self_signup": canvas_response.get("self_signup"),
            "auto_leader": canvas_response.get("auto_leader"),
            "group_limit": canvas_response.get("group_limit"),
            "created_at": (
                datetime.fromisoformat(
                    canvas_response["created_at"].replace("Z", "+00:00")
                )
                if canvas_response.get("created_at")
                else None
            ),
        },
    )

    return category, created


def update_group_category_sync(integration, category_id, name=None, self_signup=None, auto_leader=None, group_limit=None):
    """
    Update a group category in Canvas using synchronous requests.
    This function is intended for use in views where async/await is problematic.

    Args:
        integration: CanvasIntegration instance
        category_id: Canvas group category ID to update
        name: Optional - New name for the group category
        self_signup: Optional - "enabled" or "restricted"
        auto_leader: Optional - "first" or "random"
        group_limit: Optional - Maximum members per group

    Returns:
        tuple: (category, updated) - The CanvasGroupCategory instance and whether it was updated
    """
    import requests
    from datetime import datetime
    from lms.canvas.models import CanvasGroupCategory

    # Prepare the API URL and headers
    api_url = f"{integration.canvas_url}/api/v1/group_categories/{category_id}"
    headers = {
        "Authorization": f"Bearer {integration.api_key}",
        "Content-Type": "application/json",
    }

    # Convert group_limit to int if provided
    if group_limit is not None:
        try:
            group_limit = int(group_limit)
        except (ValueError, TypeError):
            group_limit = None

    # Prepare request data - only include parameters that are provided
    request_data = {}

    if name is not None:
        request_data["name"] = name

    if self_signup is not None:
        request_data["self_signup"] = self_signup

    if auto_leader is not None:
        request_data["auto_leader"] = auto_leader

    if group_limit is not None:
        request_data["group_limit"] = group_limit

    # Make the API request
    response = requests.put(api_url, json=request_data, headers=headers)

    # Check for success
    if response.status_code not in [200, 201]:
        error_msg = f"Canvas API error: {response.status_code} - {response.text}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Parse the response
    canvas_response = response.json()

    # Get the existing category
    try:
        category = CanvasGroupCategory.objects.get(canvas_id=category_id)

        # Update the fields
        if name is not None:
            category.name = name

        if self_signup is not None:
            category.self_signup = self_signup

        if auto_leader is not None:
            category.auto_leader = auto_leader

        if group_limit is not None:
            category.group_limit = group_limit

        # Save the category
        category.save()

        return category, True
    except CanvasGroupCategory.DoesNotExist:
        # Category doesn't exist locally, create it
        # First, get the course from the Canvas response
        course_id = canvas_response.get("course_id")

        if not course_id:
            error_msg = "Course ID not found in Canvas response"
            logger.error(error_msg)
            raise ValueError(error_msg)

        from lms.canvas.models import CanvasCourse
        course = CanvasCourse.objects.get(canvas_id=course_id)

        # Create the category
        category, created = CanvasGroupCategory.objects.update_or_create(
            canvas_id=category_id,
            defaults={
                "course": course,
                "name": canvas_response.get("name", "Unnamed Category"),
                "self_signup": canvas_response.get("self_signup"),
                "auto_leader": canvas_response.get("auto_leader"),
                "group_limit": canvas_response.get("group_limit"),
                "created_at": (
                    datetime.fromisoformat(
                        canvas_response["created_at"].replace("Z", "+00:00")
                    )
                    if canvas_response.get("created_at")
                    else None
                ),
            },
        )

        return category, created


def create_group_sync(integration, category_id, name, description=None):
    """
    Create a group in Canvas using synchronous requests.
    This function is intended for use in views where async/await is problematic.

    Args:
        integration: CanvasIntegration instance
        category_id: Canvas group category ID (the category/group set to add the group to)
        name: Name of the group
        description: Optional - Description of the group

    Returns:
        tuple: (group, created) - The CanvasGroup instance and whether it was created
    """
    import requests
    from datetime import datetime
    from lms.canvas.models import CanvasGroup, CanvasGroupCategory
    from django.utils import timezone

    # Prepare the API URL and headers
    api_url = f"{integration.canvas_url}/api/v1/group_categories/{category_id}/groups"
    headers = {
        "Authorization": f"Bearer {integration.api_key}",
        "Content-Type": "application/json",
    }

    # Prepare request data
    request_data = {
        "name": name
    }

    # Only add optional parameters if they have values
    if description is not None:
        request_data["description"] = description

    # Make the API request
    response = requests.post(api_url, json=request_data, headers=headers)

    # Check for success
    if response.status_code not in [200, 201]:
        error_msg = f"Canvas API error: {response.status_code} - {response.text}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Parse the response
    canvas_response = response.json()

    # Get the group category (parent) for this group
    category = CanvasGroupCategory.objects.get(canvas_id=category_id)

    # Handle description which might be None
    description_to_save = canvas_response.get("description", "")
    if description_to_save is None:
        description_to_save = ""

    # Create or update the group in our database
    group, created = CanvasGroup.objects.update_or_create(
        canvas_id=canvas_response["id"],
        defaults={
            "category": category,
            "name": canvas_response.get("name", "Unnamed Group"),
            "description": description_to_save,
            "created_at": (
                datetime.fromisoformat(
                    canvas_response["created_at"].replace("Z", "+00:00")
                )
                if canvas_response.get("created_at")
                else None
            ),
            "last_synced_at": timezone.now(),
        },
    )

    return group, created


def update_group_sync(integration, group_id, name=None, description=None, members=None):
    """
    Update a group in Canvas using synchronous requests.
    This function is intended for use in views where async/await is problematic.

    Args:
        integration: CanvasIntegration instance
        group_id: Canvas group ID to update
        name: Optional - New name for the group
        description: Optional - New description for the group
        members: Optional - List of user IDs to set as members (overwrites existing members)

    Returns:
        tuple: (group, updated) - The CanvasGroup instance and whether it was updated
    """
    import requests
    from datetime import datetime
    from lms.canvas.models import CanvasGroup
    from django.utils import timezone

    # Prepare the API URL and headers
    api_url = f"{integration.canvas_url}/api/v1/groups/{group_id}"
    headers = {
        "Authorization": f"Bearer {integration.api_key}",
        "Content-Type": "application/json",
    }

    # Prepare request data - only include parameters that are provided
    request_data = {}

    if name is not None:
        request_data["name"] = name

    if description is not None:
        request_data["description"] = description

    # When members list is provided, we'll use a special format
    # Canvas API expects members[] parameters for each member
    if members is not None and isinstance(members, list):
        # We need to switch to form data format instead of JSON for this specific case
        form_data = []
        for user_id in members:
            form_data.append(("members[]", str(user_id)))

        # If we have other parameters, add them too
        if name is not None:
            form_data.append(("name", name))
        if description is not None:
            form_data.append(("description", description))

        # Make the API request with form data
        response = requests.put(api_url, data=form_data, headers={
            "Authorization": headers["Authorization"],
        })
    else:
        # Make the API request with JSON data (normal case)
        response = requests.put(api_url, json=request_data, headers=headers)

    # Check for success
    if response.status_code not in [200, 201]:
        error_msg = f"Canvas API error: {response.status_code} - {response.text}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    # Parse the response
    canvas_response = response.json()

    # Get the existing group
    try:
        group = CanvasGroup.objects.get(canvas_id=group_id)

        # Update the fields
        if name is not None:
            group.name = name

        if description is not None:
            # Handle None description
            if description is None:
                group.description = ""
            else:
                group.description = description

        # Update the last synced timestamp
        group.last_synced_at = timezone.now()

        # Save the group
        group.save()

        return group, True
    except CanvasGroup.DoesNotExist:
        # Group doesn't exist locally, create it
        # First, get the group category from the Canvas response
        category_id = canvas_response.get("group_category_id")

        if not category_id:
            error_msg = "Group Category ID not found in Canvas response"
            logger.error(error_msg)
            raise ValueError(error_msg)

        from lms.canvas.models import CanvasGroupCategory
        try:
            category = CanvasGroupCategory.objects.get(canvas_id=category_id)
        except CanvasGroupCategory.DoesNotExist:
            error_msg = f"Group Category with ID {category_id} does not exist in the database"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # Handle description which might be None
        description_to_save = canvas_response.get("description", "")
        if description_to_save is None:
            description_to_save = ""

        # Create the group
        group, created = CanvasGroup.objects.update_or_create(
            canvas_id=group_id,
            defaults={
                "category": category,
                "name": canvas_response.get("name", "Unnamed Group"),
                "description": description_to_save,
                "created_at": (
                    datetime.fromisoformat(
                        canvas_response["created_at"].replace("Z", "+00:00")
                    )
                    if canvas_response.get("created_at")
                    else None
                ),
                "last_synced_at": timezone.now(),
            },
        )

        return group, created


def delete_group_sync(integration, group_id):
    """
    Delete a group in Canvas using synchronous requests.
    This function is intended for use in views where async/await is problematic.

    Args:
        integration: CanvasIntegration instance
        group_id: Canvas group ID to delete

    Returns:
        bool: True if deletion was successful
    """
    import requests
    from lms.canvas.models import CanvasGroup

    # Prepare the API URL and headers
    api_url = f"{integration.canvas_url}/api/v1/groups/{group_id}"
    headers = {
        "Authorization": f"Bearer {integration.api_key}",
        "Content-Type": "application/json",
    }

    # Make the API request
    response = requests.delete(api_url, headers=headers)

    # Check for success - Canvas returns 200 status code for successful deletion
    if response.status_code not in [200, 204]:
        error_msg = f"Canvas API error: {response.status_code} - {response.text}"
        logger.error(error_msg)
        # If group doesn't exist in Canvas (404), we'll still delete it locally
        if response.status_code != 404:
            raise ValueError(error_msg)

    # The group is deleted in Canvas, or doesn't exist there
    # We need to delete it from our database too

    try:
        # Get the group
        group = CanvasGroup.objects.get(canvas_id=group_id)
        group_name = group.name

        # Delete it
        group.delete()

        return True
    except CanvasGroup.DoesNotExist:
        # If the group doesn't exist in our database, it's already deleted
        logger.warning(
            f"Group with Canvas ID {group_id} does not exist in the database")
        return True


def delete_group_category_sync(integration, category_id):
    """
    Delete a group category in Canvas using synchronous requests.
    This function is intended for use in views where async/await is problematic.

    Args:
        integration: CanvasIntegration instance
        category_id: Canvas group category ID to delete

    Returns:
        bool: True if deletion was successful
    """
    import requests
    from lms.canvas.models import CanvasGroupCategory

    # Prepare the API URL and headers
    api_url = f"{integration.canvas_url}/api/v1/group_categories/{category_id}"
    headers = {
        "Authorization": f"Bearer {integration.api_key}",
        "Content-Type": "application/json",
    }

    # Make the API request
    response = requests.delete(api_url, headers=headers)

    # Check for success - Canvas returns 200 status code for successful deletion
    if response.status_code not in [200, 204]:
        error_msg = f"Canvas API error: {response.status_code} - {response.text}"
        logger.error(error_msg)
        # If category doesn't exist in Canvas (404), we'll still delete it locally
        if response.status_code != 404:
            raise ValueError(error_msg)

    # The category is deleted in Canvas, or doesn't exist there
    # We need to delete it from our database too

    try:
        # Get the category
        category = CanvasGroupCategory.objects.get(canvas_id=category_id)
        category_name = category.name

        # Delete it
        category.delete()

        return True
    except CanvasGroupCategory.DoesNotExist:
        # If the category doesn't exist in our database, it's already deleted
        logger.warning(
            f"Group category with Canvas ID {category_id} does not exist in the database")
        return True


def push_group_memberships_sync(integration, group_id, user_ids):
    """
    Push group memberships to Canvas synchronously.
    This updates the group members in Canvas to match the provided user IDs.

    Args:
        integration: CanvasIntegration instance
        group_id: Canvas group ID to update members for
        user_ids: List of Canvas user IDs to set as members (overwrites existing members)

    Returns:
        bool: True if update was successful
    """
    import requests

    # Prepare the API URL and headers
    api_url = f"{integration.canvas_url}/api/v1/groups/{group_id}"
    headers = {
        "Authorization": f"Bearer {integration.api_key}",
    }

    # Canvas API expects members[] parameters for each member
    form_data = []
    for user_id in user_ids:
        form_data.append(("members[]", str(user_id)))

    # Make the API request with form data
    response = requests.put(api_url, data=form_data, headers=headers)

    # Check for success
    if response.status_code not in [200, 201]:
        error_msg = f"Canvas API error: {response.status_code} - {response.text}"
        logger.error(error_msg)
        raise ValueError(error_msg)

    return True


def push_all_group_memberships_sync(integration, course_id):
    """
    Push all group memberships for a course to Canvas synchronously.
    This ensures that the Canvas group memberships match our local database.

    Args:
        integration: CanvasIntegration instance
        course_id: Canvas course ID

    Returns:
        dict: Summary of the operation with counts
    """
    from lms.canvas.models import CanvasCourse, CanvasGroup, CanvasGroupMembership

    # Get the course
    course = CanvasCourse.objects.get(canvas_id=course_id)

    # Track statistics
    stats = {
        "groups_updated": 0,
        "errors": 0,
    }

    # Get all groups for this course
    groups = CanvasGroup.objects.filter(category__course=course)

    for group in groups:
        try:
            # Get all memberships for this group
            memberships = CanvasGroupMembership.objects.filter(group=group)
            user_ids = [membership.user_id for membership in memberships]

            # Only push if there are members to assign
            if user_ids:
                # Push to Canvas
                push_group_memberships_sync(
                    integration, group.canvas_id, user_ids)
                stats["groups_updated"] += 1

        except Exception as e:
            logger.error(
                f"Error pushing memberships for group {group.name}: {str(e)}")
            stats["errors"] += 1

    return stats


async def push_group_memberships_async(integration, group_id, user_ids):
    """
    Push group memberships to Canvas asynchronously.
    This updates the group members in Canvas to match the provided user IDs.

    Args:
        integration: CanvasIntegration instance
        group_id: Canvas group ID to update members for
        user_ids: List of Canvas user IDs to set as members (overwrites existing members)

    Returns:
        dict: Canvas API response or True if successful
    """
    from lms.canvas.client import Client

    # Create a Canvas API client with the provided integration
    client = Client(integration)

    try:
        # Use the client's update_group method which is already async-safe
        response = await client.set_group_members(group_id, user_ids)
        return response
    except Exception as e:
        error_msg = f"Canvas API error: {str(e)}"
        logger.error(error_msg)
        raise ValueError(error_msg)


async def push_all_group_memberships_async(integration, course_id, user_id=None, update_progress=None):
    """
    Push all group memberships for a course to Canvas asynchronously.
    This ensures that the Canvas group memberships match our local database.

    Args:
        integration: CanvasIntegration instance
        course_id: Canvas course ID
        user_id: Optional user ID for progress tracking
        update_progress: Optional callback function for progress updates

    Returns:
        dict: Summary of the operation with counts
    """
    from asgiref.sync import sync_to_async
    from lms.canvas.models import CanvasCourse, CanvasGroup, CanvasGroupMembership
    from lms.canvas.progress import SyncProgress

    # Get the course
    course = await sync_to_async(CanvasCourse.objects.get)(canvas_id=course_id)

    # Track statistics
    stats = {
        "groups_updated": 0,
        "errors": 0,
        "total_groups": 0,
    }

    # Get all groups for this course
    groups = await sync_to_async(lambda: list(CanvasGroup.objects.filter(category__course=course)))()
    total_groups = len(groups)
    stats["total_groups"] = total_groups

    # Initialize progress tracking if user_id is provided
    if user_id:
        await SyncProgress.async_start_sync(user_id, course_id, total_steps=total_groups)
        await SyncProgress.async_update(
            user_id,
            course_id,
            current=0,
            total=total_groups,
            status=SyncProgress.STATUS_IN_PROGRESS,
            message=f"Starting to push memberships for {total_groups} groups..."
        )

    # Process groups sequentially to avoid issues with mixing sync/async code
    for idx, group in enumerate(groups):
        # Process each group
        await process_group_memberships(integration, group, stats, user_id, total_groups, idx)

        # Update progress every few groups to avoid too many DB operations
        if user_id and (idx % 3 == 0 or idx == total_groups - 1):
            current_progress = idx + 1
            percent_complete = int((current_progress / total_groups) * 100)
            message = f"Processed {current_progress} of {total_groups} groups"

            await SyncProgress.async_update(
                user_id,
                course_id,
                current=current_progress,
                total=total_groups,
                status=SyncProgress.STATUS_IN_PROGRESS,
                message=message
            )

            # Call the progress callback if provided
            if update_progress:
                await update_progress(SyncProgress.STATUS_IN_PROGRESS, message, percent_complete)

    # Complete progress tracking if user_id is provided
    if user_id:
        success = stats["errors"] == 0
        message = f"Successfully pushed memberships for {stats['groups_updated']} groups"
        error = None

        if not success:
            message = f"Pushed memberships with {stats['errors']} errors out of {total_groups} groups"
            error = f"Encountered {stats['errors']} errors during push"

        await SyncProgress.async_complete_sync(
            user_id,
            course_id,
            success=success,
            message=message,
            error=error
        )

    return stats


async def process_group_memberships(integration, group, stats, user_id, total_groups, current_index):
    """
    Process memberships for a single group asynchronously.
    Helper function for push_all_group_memberships_async.

    Args:
        integration: CanvasIntegration instance
        group: CanvasGroup instance to process
        stats: Statistics dictionary to update
        user_id: Optional user ID for progress tracking
        total_groups: Total number of groups being processed
        current_index: Current index of this group in the overall process

    Returns:
        None, but updates the stats dictionary in place
    """
    from asgiref.sync import sync_to_async
    from lms.canvas.models import CanvasGroupMembership
    from lms.canvas.progress import SyncProgress

    try:
        # Get all memberships for this group
        memberships = await sync_to_async(lambda: list(CanvasGroupMembership.objects.filter(group=group)))()
        user_ids = [membership.user_id for membership in memberships]

        # Only push if there are members to assign
        if user_ids:
            # Update progress if user_id is provided
            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    None,  # No course_id for individual group updates
                    current=current_index,
                    total=total_groups,
                    status="pushing_memberships",
                    message=f"Pushing memberships for group: {group.name}"
                )

            # Push to Canvas using the safer Canvas Client
            await push_group_memberships_async(integration, group.canvas_id, user_ids)
            stats["groups_updated"] += 1
            logger.info(f"Successfully pushed {len(user_ids)} memberships for group {group.name}")

    except Exception as e:
        logger.error(f"Error pushing memberships for group {group.name}: {str(e)}")
        logger.exception("Full stack trace:")
        stats["errors"] += 1
