"""
Sync service for Canvas API data.
"""

import logging
import traceback
from typing import List, Dict, Optional, Union, Tuple, Any
from django.utils import timezone
from asgiref.sync import sync_to_async

from lms.canvas.client import Client
from lms.canvas.models import (
    CanvasCourse,
    CanvasEnrollment,
    CanvasGroupCategory,
    CanvasGroup,
    CanvasGroupMembership,
)
from core.models import Student, Team
from lms.utils import SafeAsyncAccessor

logger = logging.getLogger(__name__)


class CanvasSyncer:
    """Service for syncing Canvas data with the application models"""

    def __init__(self, client: Client):
        self.client = client

    async def sync_canvas_groups(self, course: CanvasCourse, user_id=None) -> List[int]:
        """
        Sync Canvas groups for a course to Teams

        Args:
            course: CanvasCourse to sync groups for
            user_id: Optional user ID for progress tracking

        Returns:
            List of Canvas group IDs that were synced
        """
        from .progress import SyncProgress
        import traceback

        if user_id:
            await SyncProgress.async_update(
                user_id,
                course.canvas_id,
                status="fetching_groups",
                message="Fetching group categories from Canvas...",
            )

        try:
            # 1. Fetch group categories
            logger.info(
                f"Fetching group categories for course {course.name} (ID: {course.canvas_id})"
            )
            categories = await self.client.get_group_categories(course.canvas_id)
            logger.info(
                f"Found {len(categories)} group categories in course {course.name}"
            )

            # Track all Canvas group IDs to handle cleanup later
            current_group_ids = []

            # 2. Upsert Teams for each Canvas group
            for cat in categories:
                logger.info(
                    f"Processing category: {cat.get('name')} (ID: {cat.get('id')})"
                )
                try:
                    # Save category
                    category = await self.client._save_group_category(cat, course)
                    logger.info(f"Saved category {category.name} (ID: {category.id})")

                    if user_id:
                        await SyncProgress.async_update(
                            user_id,
                            course.canvas_id,
                            status="fetching_groups",
                            message=f"Fetching groups in category: {cat.get('name', 'Unnamed Category')}",
                        )

                    # Get groups in this category
                    groups = await self.client.get_groups(cat["id"])
                    logger.info(
                        f"Found {len(groups)} groups in category {category.name}"
                    )

                    if user_id and groups:
                        await SyncProgress.async_update(
                            user_id,
                            course.canvas_id,
                            status="saving_groups",
                            message=f"Saving {len(groups)} groups to database...",
                        )

                    # Process each group
                    for grp in groups:
                        logger.info(
                            f"Processing group: {grp.get('name')} (ID: {grp.get('id')})"
                        )
                        try:
                            current_group_ids.append(grp["id"])

                            # Save the Canvas group
                            canvas_group = await self.client._save_group(grp, category)
                            logger.info(
                                f"Saved Canvas group {canvas_group.name} (ID: {canvas_group.id})"
                            )

                            # Update or create team with timestamp
                            # Safely handle description which might be None
                            description = grp.get("description", "")
                            if description is None:
                                description = ""

                            team, created = await Team.objects.aupdate_or_create(
                                canvas_group_id=grp["id"],
                                canvas_course=course,
                                defaults={
                                    "name": grp.get("name", "")[:100],
                                    "description": description,
                                    "canvas_group_set_id": cat.get("id"),
                                    "canvas_group_set_name": cat.get("name", ""),
                                },
                            )
                            logger.info(
                                f"{'Created' if created else 'Updated'} team {team.name} (ID: {team.id})"
                            )

                            # Link team to Canvas group - using SafeAsyncAccessor to avoid async context errors
                            core_team = await SafeAsyncAccessor.get_attr(
                                canvas_group, "core_team"
                            )

                            if core_team != team:
                                canvas_group.core_team = team
                                await canvas_group.asave(update_fields=["core_team"])
                                logger.info(
                                    f"Linked Canvas group {canvas_group.name} to team {team.name}"
                                )

                            # Log when new teams are created
                            if created:
                                logger.info(
                                    f"Created new team from Canvas group: {team.name} (ID: {grp['id']})"
                                )
                        except Exception as e:
                            logger.error(
                                f"Error processing group {grp.get('name', 'unknown')} (ID: {grp.get('id', 'unknown')}): {e}"
                            )
                            logger.error(traceback.format_exc())
                            # Continue with next group
                except Exception as e:
                    logger.error(
                        f"Error processing category {cat.get('name', 'unknown')} (ID: {cat.get('id', 'unknown')}): {e}"
                    )
                    logger.error(traceback.format_exc())
                    # Continue with next category

            # Return group IDs for potential cleanup
            logger.info(
                f"Completed syncing {len(current_group_ids)} groups for course {course.name}"
            )
            return current_group_ids
        except Exception as e:
            logger.error(f"Error syncing Canvas groups for course {course.name}: {e}")
            logger.error(traceback.format_exc())
            # Return empty list to indicate no groups were synced
            return []

    async def sync_group_memberships(self, course: CanvasCourse, user_id=None):
        """
        Sync group memberships to Student.team assignments

        Args:
            course: CanvasCourse to sync group memberships for
            user_id: Optional user ID for progress tracking
        """
        from .progress import SyncProgress

        # 3. Assign students to teams based on membership
        # Convert query to list with async iteration
        teams = []
        async for team in Team.objects.filter(
            canvas_course=course, canvas_group_id__isnull=False
        ):
            teams.append(team)

        if user_id:
            await SyncProgress.async_update(
                user_id,
                course.canvas_id,
                status="syncing_members",
                message=f"Syncing memberships for {len(teams)} teams...",
            )

        for i, team in enumerate(teams):
            if not team.canvas_group_id:
                continue  # Skip manually created teams

            if user_id and i > 0 and i % 5 == 0:
                await SyncProgress.async_update(
                    user_id,
                    course.canvas_id,
                    status="syncing_members",
                    message=f"Syncing team {i+1} of {len(teams)}: {team.name}",
                )

            try:
                # Find the associated Canvas group
                canvas_group = await CanvasGroup.objects.aget(
                    canvas_id=team.canvas_group_id
                )

                # Get more detailed member information including email
                members = await self.client.get_group_members(team.canvas_group_id)

                if logger:
                    logger.info(
                        f"Found {len(members)} members in Canvas group {team.name} (ID: {team.canvas_group_id})"
                    )

                for m in members:
                    # Save the group membership record first regardless of enrollment
                    # This ensures we capture all group members even if not enrolled
                    await self.client._save_group_membership(m, canvas_group)

                    # Now try to find enrollment to link the student to the team
                    try:
                        enroll = await CanvasEnrollment.objects.aget(
                            user_id=m["id"], course=course
                        )
                    except CanvasEnrollment.DoesNotExist:
                        # We'll still create the membership, but won't link to a student
                        if logger:
                            logger.warning(
                                f"Enrollment not found for user ID {m['id']} in team {team.name}"
                            )
                        continue

                    # Link or create Student, then assign team - use SafeAsyncAccessor to avoid async context errors
                    student = await SafeAsyncAccessor.get_attr(enroll, "student")

                    if not student:
                        # Handle potential missing data with safe defaults
                        try:
                            # Get enrollment attributes safely
                            user_name = await SafeAsyncAccessor.get_attr(
                                enroll, "user_name"
                            )
                            email = await SafeAsyncAccessor.get_attr(enroll, "email")
                            user_id = await SafeAsyncAccessor.get_attr(
                                enroll, "user_id"
                            )

                            # Parse user name
                            user_name_parts = user_name.split()
                            first_name = (
                                user_name_parts[0] if user_name_parts else "Unknown"
                            )
                            last_name = (
                                " ".join(user_name_parts[1:])
                                if len(user_name_parts) > 1
                                else ""
                            )

                            # Ensure email has a fallback
                            email = email or f"canvas-user-{user_id}@example.com"

                            # Create or update student
                            student, created = await Student.objects.aupdate_or_create(
                                canvas_user_id=str(user_id),
                                defaults={
                                    "email": email,
                                    "first_name": first_name,
                                    "last_name": last_name,
                                },
                            )

                            # Log new student creation
                            if created and logger:
                                student_name = await SafeAsyncAccessor.get_attr(
                                    student, "full_name"
                                )
                                logger.info(
                                    f"Created new student from Canvas enrollment: {student_name}"
                                )

                            # Link student to enrollment
                            enroll.student = student
                            await enroll.asave(update_fields=["student"])
                        except Exception as e:
                            if logger:
                                enroll_id = await SafeAsyncAccessor.get_attr(
                                    enroll, "id"
                                )
                                logger.error(
                                    f"Error creating student for enrollment {enroll_id}: {str(e)}"
                                )
                            continue

                    # Only update if team has changed
                    current_team = await SafeAsyncAccessor.get_attr(student, "team")

                    if current_team != team:
                        # Get old team name for logging
                        old_team_name = "None"
                        if current_team:
                            old_team_name = await SafeAsyncAccessor.get_attr(
                                current_team, "name"
                            )

                        # Update team
                        student.team = team
                        await student.asave(update_fields=["team"])

                        # Get student name for logging
                        student_name = await SafeAsyncAccessor.get_attr(
                            student, "full_name"
                        )

                        if logger:
                            logger.info(
                                f"Updated student {student_name} team assignment: "
                                + f"{old_team_name} → {team.name}"
                            )
            except Exception as e:
                if logger:
                    logger.error(
                        f"Error syncing memberships for team {team.name}: {str(e)}"
                    )
                continue

    async def push_group_assignments(self, course: CanvasCourse):
        """
        Push local Team → Canvas group assignments back to Canvas

        Args:
            course: CanvasCourse to push group assignments for
        """
        # For each imported Team, gather current members and send to Canvas
        async for team in Team.objects.filter(
            canvas_course=course, canvas_group_id__isnull=False
        ):
            user_ids = []

            # Get all student IDs for this team
            async for student in Student.objects.filter(team=team):
                # Find their Canvas enrollment
                try:
                    enrollment = await CanvasEnrollment.objects.aget(
                        student=student, course=course
                    )
                    user_ids.append(int(enrollment.user_id))
                except CanvasEnrollment.DoesNotExist:
                    continue

            # Only update if we have members to add
            if user_ids:
                await self.client.set_group_members(team.canvas_group_id, user_ids)
