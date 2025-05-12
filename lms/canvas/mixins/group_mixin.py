# File: lms/canvas/mixins/group_mixin.py
"""
Mixin providing group and category related methods for Canvas API client.
"""
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class GroupMixin:
    """Provides group and category related API methods"""

    async def get_group_categories(self, course_id: int) -> List[Dict]:
        """Get all group categories for a course"""
        return await self.request(
            "GET", f"courses/{course_id}/group_categories", params={"per_page": 100}
        )

    async def get_groups(self, category_id: int) -> List[Dict]:
        """Get all groups for a category"""
        return await self.request(
            "GET", f"group_categories/{category_id}/groups", params={"per_page": 100}
        )

    async def get_group_members(self, group_id: int) -> List[Dict]:
        """Get all members for a group with detailed information including email"""
        return await self.request(
            "GET",
            f"groups/{group_id}/users",
            params={
                "per_page": 100,
                "include[]": ["email", "avatar_url", "bio", "enrollments"],
            },
        )

    async def invite_user_to_group(self, group_id: int, user_ids: List[int]):
        """Invite users to a group"""
        return await self.request(
            "POST", f"groups/{group_id}/invite", data={"invitees[]": user_ids}
        )

    async def set_group_members(self, group_id: int, user_ids: List[int]):
        """Set the members of a group (overwrites existing members)"""
        return await self.request(
            "PUT", f"groups/{group_id}", data=[("members[]", uid) for uid in user_ids]
        )

    async def assign_unassigned(self, category_id: int, sync: bool = True):
        """Assign unassigned members to groups in a category"""
        params = {"sync": "true"} if sync else {}
        return await self.request(
            "POST",
            f"group_categories/{category_id}/assign_unassigned_members",
            params=params,
        )

    async def create_group_category(
            self, course_id: int, name: str, self_signup: Optional[str] = None,
            auto_leader: Optional[str] = None, group_limit: Optional[int] = None
    ):
        """
        Create a new group category (group set) in Canvas

        Args:
            course_id: Canvas course ID
            name: The name of the group category
            self_signup: "enabled" or "restricted" - whether students can sign up for a group themselves
            auto_leader: "first" or "random" - assigns group leader automatically
            group_limit: Maximum number of members per group

        Returns:
            The created group category data from Canvas
        """
        # Build data for API request
        category_data = {"name": name}

        # Only add optional parameters if they are provided
        if self_signup:
            category_data["self_signup"] = self_signup

        if auto_leader:
            category_data["auto_leader"] = auto_leader

        if group_limit is not None:
            category_data["group_limit"] = group_limit

        # Make the API request
        response = await self.request(
            "POST", f"courses/{course_id}/group_categories", data=category_data
        )

        # Save to our database
        course = await self.models.CanvasCourse.objects.aget(canvas_id=course_id)
        await self._save_group_category(response, course)

        return response

    async def update_group_category(
            self, category_id: int, name: Optional[str] = None, self_signup: Optional[str] = None,
            auto_leader: Optional[str] = None, group_limit: Optional[int] = None
    ):
        """
        Update an existing group category (group set) in Canvas

        Args:
            category_id: Canvas group category ID
            name: The name of the group category
            self_signup: "enabled" or "restricted" - whether students can sign up for a group themselves
            auto_leader: "first" or "random" - assigns group leader automatically
            group_limit: Maximum number of members per group

        Returns:
            The updated group category data from Canvas
        """
        # Build data for API request
        category_data = {}

        # Only add parameters if they are provided
        if name is not None:
            category_data["name"] = name

        if self_signup is not None:
            category_data["self_signup"] = self_signup

        if auto_leader is not None:
            category_data["auto_leader"] = auto_leader

        if group_limit is not None:
            category_data["group_limit"] = group_limit

        # Make the API request
        response = await self.request(
            "PUT", f"group_categories/{category_id}", data=category_data
        )

        # Get the course to pass to the save method
        # First fetch the category to get its course
        try:
            category = await self.models.CanvasGroupCategory.objects.aget(canvas_id=category_id)
            course = category.course
            await self._save_group_category(response, course)
        except self.models.CanvasGroupCategory.DoesNotExist:
            # If category doesn't exist locally yet, just log and continue
            logger.warning(
                f"Tried to update group category {category_id} which doesn't exist locally")

        return response

    async def create_group(
            self, category_id: int, name: str, description: Optional[str] = None
    ):
        """
        Create a new group within a group category in Canvas

        Args:
            category_id: Canvas group category ID
            name: The name of the group
            description: Optional description of the group

        Returns:
            The created group data from Canvas
        """
        # Build data for API request
        group_data = {"name": name}

        if description:
            group_data["description"] = description

        # Make the API request
        response = await self.request(
            "POST", f"group_categories/{category_id}/groups", data=group_data
        )

        # Save to our database
        try:
            category = await self.models.CanvasGroupCategory.objects.aget(canvas_id=category_id)
            await self._save_group(response, category)
        except self.models.CanvasGroupCategory.DoesNotExist:
            # If category doesn't exist locally yet, just log and continue
            logger.warning(
                f"Tried to create group in category {category_id} which doesn't exist locally")

        return response

    async def update_group(
            self, group_id: int, name: Optional[str] = None, description: Optional[str] = None,
            members: Optional[List[int]] = None
    ):
        """
        Update an existing group in Canvas

        Args:
            group_id: Canvas group ID
            name: The name of the group
            description: Description of the group
            members: List of user IDs to set as members (overwrites existing members)

        Returns:
            The updated group data from Canvas
        """
        # Build data for API request
        group_data = {}

        if name is not None:
            group_data["name"] = name

        if description is not None:
            group_data["description"] = description

        # Handle members separately - they need to be passed as members[]
        if members is not None:
            group_data = [("members[]", user_id) for user_id in members]
            # If we have other parameters, add them to the form data
            if name is not None:
                group_data.append(("name", name))
            if description is not None:
                group_data.append(("description", description))

        # Make the API request
        response = await self.request(
            "PUT", f"groups/{group_id}", data=group_data
        )

        # Update in our database
        try:
            group = await self.models.CanvasGroup.objects.aget(canvas_id=group_id)
            category = group.category
            await self._save_group(response, category)
        except self.models.CanvasGroup.DoesNotExist:
            # If group doesn't exist locally yet, just log and continue
            logger.warning(
                f"Tried to update group {group_id} which doesn't exist locally")

        return response

    async def _save_group_category(self, category_data: Dict, course: 'CanvasCourse'):
        """Save group category data to the database using native async ORM"""
        category, created = await self.models.CanvasGroupCategory.objects.aupdate_or_create(
            canvas_id=category_data["id"],
            defaults={
                "course": course,
                "name": category_data.get("name", "Unnamed Category"),
                "self_signup": category_data.get("self_signup"),
                "auto_leader": category_data.get("auto_leader"),
                "group_limit": category_data.get("group_limit"),
                "created_at": (
                    datetime.fromisoformat(
                        category_data["created_at"].replace("Z", "+00:00")
                    )
                    if category_data.get("created_at")
                    else None
                ),
            },
        )
        return category

    async def _save_group(self, group_data: Dict, category):
        """Save group data to the database using native async ORM"""
        # Safely handle description which might be None
        description = group_data.get("description", "")
        if description is None:
            description = ""

        group, created = await self.models.CanvasGroup.objects.aupdate_or_create(
            canvas_id=group_data["id"],
            defaults={
                "category": category,
                "name": group_data.get("name", "Unnamed Group"),
                "description": description,
                "created_at": (
                    datetime.fromisoformat(
                        group_data["created_at"].replace("Z", "+00:00")
                    )
                    if group_data.get("created_at")
                    else None
                ),
                "last_synced_at": self.timezone.now(),
            },
        )
        return group

    async def _save_group_membership(self, member_data: Dict, group):
        """Save group membership data to the database using native async ORM"""
        # Try to find matching student - first by canvas_user_id
        student = None
        if "id" in member_data:
            try:
                # First try exact match by canvas_user_id
                student = await self.models.Student.objects.filter(
                    canvas_user_id=str(member_data["id"])
                ).afirst()

                # If student not found, try to find by enrollment
                if student is None:
                    # Look for enrollment with this user_id to find a linked student
                    enrollment = await self.models.CanvasEnrollment.objects.filter(
                        user_id=member_data["id"], course=group.category.course
                    ).afirst()

                    if enrollment and enrollment.student:
                        student = enrollment.student
                        # Update the student's canvas_user_id for future lookups
                        if not student.canvas_user_id:
                            student.canvas_user_id = str(member_data["id"])
                            # Use async save
                            await student.asave(update_fields=["canvas_user_id"])
                            logger.info(
                                f"Updated student {student.full_name} with Canvas user ID {member_data['id']}"
                            )

                # If still not found, look by email as a last resort
                if student is None and member_data.get("email"):
                    student = await self.models.Student.objects.filter(
                        email=member_data["email"]
                    ).afirst()
                    if student:
                        # Update the student's canvas_user_id
                        student.canvas_user_id = str(member_data["id"])
                        await student.asave(update_fields=["canvas_user_id"])
                        logger.info(
                            f"Matched student {student.full_name} by email with Canvas user ID {member_data['id']}"
                        )

            except Exception as e:
                logger.error(
                    f"Error finding student for member {member_data.get('name')}: {str(e)}"
                )

        membership, created = await self.models.CanvasGroupMembership.objects.aupdate_or_create(
            group=group,
            user_id=member_data["id"],
            defaults={
                "student": student,
                "name": member_data.get(
                    "name", member_data.get("display_name", "Unknown")
                ),
                "email": member_data.get("email"),
            },
        )

        if created:
            logger.info(
                f"Created new group membership for {membership.name} in {group.name}"
            )

        return membership