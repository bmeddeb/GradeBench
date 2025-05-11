"""
Sync service for Canvas API data.
"""
import logging
from typing import List, Dict, Optional
from django.utils import timezone

from lms.canvas.client import Client
from lms.canvas.models import (
    CanvasCourse, CanvasEnrollment, CanvasGroupCategory, 
    CanvasGroup, CanvasGroupMembership
)
from core.models import Student, Team

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

        if user_id:
            await SyncProgress.async_update(
                user_id, course.canvas_id,
                status="fetching_groups",
                message="Fetching group categories from Canvas..."
            )

        # 1. Fetch group‑sets
        categories = await self.client.get_group_categories(course.canvas_id)

        # Track all Canvas group IDs to handle cleanup later
        current_group_ids = []

        # 2. Upsert Teams for each Canvas group
        for cat in categories:
            # Save category
            category = await self.client._save_group_category(cat, course)
            
            if user_id:
                await SyncProgress.async_update(
                    user_id, course.canvas_id,
                    status="fetching_groups",
                    message=f"Fetching groups in category: {cat.get('name', 'Unnamed Category')}"
                )

            groups = await self.client.get_groups(cat['id'])

            if user_id and groups:
                await SyncProgress.async_update(
                    user_id, course.canvas_id,
                    status="saving_groups",
                    message=f"Saving {len(groups)} groups to database..."
                )

            for grp in groups:
                current_group_ids.append(grp['id'])

                # Save the Canvas group
                canvas_group = await self.client._save_group(grp, category)

                # Update or create team with timestamp
                team, created = await Team.objects.aupdate_or_acreate(
                    canvas_group_id=grp['id'],
                    canvas_course=course,
                    defaults={
                        'name': grp.get('name')[:100],
                        'description': grp.get('description','')[:500],
                        'last_synced_at': timezone.now()
                    }
                )
                
                # Link team to Canvas group
                if canvas_group.core_team != team:
                    canvas_group.core_team = team
                    await canvas_group.asave(update_fields=['core_team'])

                # Log when new teams are created
                if created and logger:
                    logger.info(f"Created new team from Canvas group: {team.name} (ID: {grp['id']})")

        # Return group IDs for potential cleanup
        return current_group_ids

    async def sync_group_memberships(self, course: CanvasCourse, user_id=None):
        """
        Sync group memberships to Student.team assignments
        
        Args:
            course: CanvasCourse to sync group memberships for
            user_id: Optional user ID for progress tracking
        """
        from .progress import SyncProgress

        # 3. Assign students to teams based on membership
        teams = await Team.objects.filter(
            canvas_course=course, 
            canvas_group_id__isnull=False
        ).to_list()

        if user_id:
            await SyncProgress.async_update(
                user_id, course.canvas_id,
                status="syncing_members",
                message=f"Syncing memberships for {len(teams)} teams..."
            )

        for i, team in enumerate(teams):
            if not team.canvas_group_id:
                continue  # Skip manually created teams

            if user_id and i > 0 and i % 5 == 0:
                await SyncProgress.async_update(
                    user_id, course.canvas_id,
                    status="syncing_members",
                    message=f"Syncing team {i+1} of {len(teams)}: {team.name}"
                )

            try:
                # Find the associated Canvas group
                canvas_group = await CanvasGroup.objects.aget(
                    canvas_id=team.canvas_group_id
                )
                
                members = await self.client.get_group_members(team.canvas_group_id)

                for m in members:
                    try:
                        enroll = await CanvasEnrollment.objects.aget(
                            user_id=m['id'], course=course)
                    except CanvasEnrollment.DoesNotExist:
                        if logger:
                            logger.warning(
                                f"Enrollment not found for user ID {m['id']} in team {team.name}"
                            )
                        continue

                    # Save the group membership record
                    await self.client._save_group_membership(m, canvas_group)

                    # Link or create Student, then assign team
                    student = enroll.student
                    if not student:
                        # Handle potential missing data with safe defaults
                        try:
                            user_name_parts = enroll.user_name.split()
                            first_name = user_name_parts[0] if user_name_parts else "Unknown"
                            last_name = " ".join(user_name_parts[1:]) if len(user_name_parts) > 1 else ""

                            student, created = await Student.objects.aupdate_or_acreate(
                                canvas_user_id=str(enroll.user_id),
                                defaults={
                                    'email': enroll.email or f"canvas-user-{enroll.user_id}@example.com",
                                    'first_name': first_name,
                                    'last_name': last_name,
                                }
                            )

                            if created and logger:
                                logger.info(f"Created new student from Canvas enrollment: {student.full_name}")

                            enroll.student = student
                            await enroll.asave(update_fields=['student'])
                        except Exception as e:
                            if logger:
                                logger.error(f"Error creating student for enrollment {enroll.id}: {str(e)}")
                            continue

                    # Only update if team has changed
                    if student.team != team:
                        old_team = student.team
                        student.team = team
                        await student.asave(update_fields=['team'])

                        if logger:
                            logger.info(
                                f"Updated student {student.full_name} team assignment: " +
                                f"{old_team.name if old_team else 'None'} → {team.name}"
                            )
            except Exception as e:
                if logger:
                    logger.error(f"Error syncing memberships for team {team.name}: {str(e)}")
                continue

    async def push_group_assignments(self, course: CanvasCourse):
        """
        Push local Team → Canvas group assignments back to Canvas
        
        Args:
            course: CanvasCourse to push group assignments for
        """
        # For each imported Team, gather current members and send to Canvas
        async for team in Team.objects.filter(canvas_course=course, canvas_group_id__isnull=False):
            user_ids = []
            
            # Get all student IDs for this team
            async for student in Student.objects.filter(team=team):
                # Find their Canvas enrollment
                try:
                    enrollment = await CanvasEnrollment.objects.aget(
                        student=student, 
                        course=course
                    )
                    user_ids.append(int(enrollment.user_id))
                except CanvasEnrollment.DoesNotExist:
                    continue
            
            # Only update if we have members to add
            if user_ids:
                await self.client.set_group_members(team.canvas_group_id, user_ids)