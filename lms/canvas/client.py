# lms/canvas/client.py

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import httpx
from asgiref.sync import sync_to_async


from .models import (
    CanvasAssignment,
    CanvasCourse,
    CanvasEnrollment,
    CanvasIntegration,
    CanvasRubric,
    CanvasRubricCriterion,
    CanvasRubricRating,
    CanvasSubmission,
)

logger = logging.getLogger(__name__)


class Client:
    """Async client for interacting with the Canvas API"""

    def __init__(self, integration: CanvasIntegration):
        """Initialize with a CanvasIntegration instance"""
        self.integration = integration
        self.base_url = integration.canvas_url
        self.api_key = integration.api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
    ) -> Any:
        """Make an async request to the Canvas API using httpx"""
        url = f"{self.base_url}/api/v1/{endpoint}"
        params = params or {}
        data = data or {}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=data if method.lower() in ["post", "put"] else None,
                )
                response.raise_for_status()

                result = response.json()
                if isinstance(result, list) and "link" in response.headers:
                    while "next" in response.headers.get("link", ""):
                        links = response.headers.get("link").split(",")
                        next_url = None
                        for link in links:
                            if 'rel="next"' in link:
                                next_url = link.split(";")[0].strip("<> ")
                                break
                        if not next_url:
                            break
                        next_response = await client.get(next_url, headers=self.headers)
                        next_response.raise_for_status()
                        next_result = next_response.json()
                        result.extend(next_result)
                        if (
                            "link" not in next_response.headers
                            or "next" not in next_response.headers.get("link", "")
                        ):
                            break
                return result
            except httpx.HTTPError as e:
                logger.error(f"API request error: {e}")
                raise

    async def get_courses(self) -> List[Dict]:
        """Get all courses for the authenticated user"""
        return await self.request(
            "GET",
            "courses",
            params={
                "include[]": [
                    "term",
                    "total_students",
                    "syllabus_body",
                    "course_image",
                ],
                "state[]": ["available", "completed", "unpublished"],
                "per_page": 100,
            },
        )

    async def get_course(self, course_id: int) -> Dict:
        """Get a single course by ID"""
        return await self.request(
            "GET",
            f"courses/{course_id}",
            params={"include[]": ["term", "syllabus_body", "course_image"]},
        )

    async def get_enrollments(self, course_id: int) -> List[Dict]:
        """Get all enrollments for a course"""
        return await self.request(
            "GET",
            f"courses/{course_id}/enrollments",
            params={
                "include[]": [
                    "avatar_url",
                    "group_ids",
                    "locked",
                    "observed_users",
                    "can_be_removed",
                    "uuid",
                    "current_grading_period_scores",
                    "user",
                ],
                "per_page": 100,
            },
        )

    async def get_course_users(self, course_id: int) -> List[Dict]:
        """Get all users (students, teachers, TAs, etc.) for a course with email information"""
        return await self.request(
            "GET",
            f"courses/{course_id}/users",
            params={"include[]": ["email", "enrollments"], "per_page": 100},
        )

    async def get_assignments(self, course_id: int) -> List[Dict]:
        """Get all assignments for a course"""
        return await self.request(
            "GET",
            f"courses/{course_id}/assignments",
            params={
                "include[]": ["submission", "rubric", "all_dates", "overrides"],
                "per_page": 100,
            },
        )

    async def get_assignment(self, course_id: int, assignment_id: int) -> Dict:
        """Get a single assignment by ID"""
        return await self.request(
            "GET",
            f"courses/{course_id}/assignments/{assignment_id}",
            params={"include[]": ["submission", "rubric", "all_dates", "overrides"]},
        )

    async def get_submissions(self, course_id: int, assignment_id: int) -> List[Dict]:
        """Get all submissions for an assignment"""
        return await self.request(
            "GET",
            f"courses/{course_id}/assignments/{assignment_id}/submissions",
            params={
                "include[]": ["user", "submission_comments", "rubric_assessment"],
                "per_page": 100,
            },
        )

    async def get_submission(
        self, course_id: int, assignment_id: int, user_id: int
    ) -> Dict:
        """Get a submission for a specific user"""
        return await self.request(
            "GET",
            f"courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}",
            params={"include[]": ["user", "submission_comments", "rubric_assessment"]},
        )

    @sync_to_async
    def _save_course(self, course_data: Dict) -> CanvasCourse:
        """Save course data to the database (sync function)"""
        course, created = CanvasCourse.objects.update_or_create(
            canvas_id=course_data["id"],
            integration=self.integration,
            defaults={
                "name": course_data["name"],
                "course_code": course_data["course_code"],
                "start_at": (
                    datetime.fromisoformat(
                        course_data["start_at"].replace("Z", "+00:00")
                    )
                    if course_data.get("start_at")
                    else None
                ),
                "end_at": (
                    datetime.fromisoformat(course_data["end_at"].replace("Z", "+00:00"))
                    if course_data.get("end_at")
                    else None
                ),
                "is_public": course_data.get("is_public", False),
                "syllabus_body": course_data.get("syllabus_body", ""),
                "workflow_state": course_data.get("workflow_state", "unpublished"),
                "time_zone": course_data.get("time_zone"),
                "uuid": course_data.get("uuid"),
            },
        )
        return course

    @sync_to_async
    def _save_enrollment(
        self, enrollment_data: Dict, course: CanvasCourse
    ) -> CanvasEnrollment:
        """Save enrollment data to the database (sync function)"""
        user_data = enrollment_data.get("user", {})

        enrollment, created = CanvasEnrollment.objects.update_or_create(
            canvas_id=enrollment_data["id"],
            course=course,
            defaults={
                "user_id": enrollment_data["user_id"],
                "user_name": user_data.get("name", "Unknown User"),
                "sortable_name": user_data.get("sortable_name"),
                "short_name": user_data.get("short_name"),
                "email": user_data.get("email"),
                "role": enrollment_data.get("role", "StudentEnrollment"),
                "enrollment_state": enrollment_data.get("enrollment_state", "active"),
                "last_activity_at": (
                    datetime.fromisoformat(
                        enrollment_data["last_activity_at"].replace("Z", "+00:00")
                    )
                    if enrollment_data.get("last_activity_at")
                    else None
                ),
                "grades": enrollment_data.get("grades", {}),
            },
        )
        return enrollment

    @sync_to_async
    def _save_assignment(
        self, assignment_data: Dict, course: CanvasCourse
    ) -> CanvasAssignment:
        """Save assignment data to the database (sync function)"""
        assignment, created = CanvasAssignment.objects.update_or_create(
            canvas_id=assignment_data["id"],
            course=course,
            defaults={
                "name": assignment_data["name"],
                "description": assignment_data.get("description", ""),
                "points_possible": assignment_data.get("points_possible", 0.0),
                "due_at": (
                    datetime.fromisoformat(
                        assignment_data["due_at"].replace("Z", "+00:00")
                    )
                    if assignment_data.get("due_at")
                    else None
                ),
                "unlock_at": (
                    datetime.fromisoformat(
                        assignment_data["unlock_at"].replace("Z", "+00:00")
                    )
                    if assignment_data.get("unlock_at")
                    else None
                ),
                "lock_at": (
                    datetime.fromisoformat(
                        assignment_data["lock_at"].replace("Z", "+00:00")
                    )
                    if assignment_data.get("lock_at")
                    else None
                ),
                "position": assignment_data.get("position", 0),
                "grading_type": assignment_data.get("grading_type", "points"),
                "published": assignment_data.get("published", False),
                "submission_types": assignment_data.get("submission_types", []),
                "has_submitted_submissions": assignment_data.get(
                    "has_submitted_submissions", False
                ),
                "muted": assignment_data.get("muted", False),
                "html_url": assignment_data.get("html_url", ""),
                "has_overrides": assignment_data.get("has_overrides", False),
                "needs_grading_count": assignment_data.get("needs_grading_count", 0),
                "is_quiz_assignment": assignment_data.get("is_quiz_assignment", False),
            },
        )

        # If the assignment has a rubric, save it
        if (
            "rubric" in assignment_data
            and assignment_data["rubric"]
            and "rubric_settings" in assignment_data
        ):
            rubric_settings = assignment_data["rubric_settings"]
            rubric, _ = CanvasRubric.objects.update_or_create(
                canvas_id=str(rubric_settings["id"]),
                defaults={
                    "title": rubric_settings.get("title", "Untitled Rubric"),
                    "points_possible": rubric_settings.get("points_possible", 0.0),
                },
            )

            # Save criteria and ratings
            for criterion_data in assignment_data["rubric"]:
                criterion, _ = CanvasRubricCriterion.objects.update_or_create(
                    rubric=rubric,
                    canvas_id=criterion_data["id"],
                    defaults={
                        "description": criterion_data.get("description", ""),
                        "long_description": criterion_data.get("long_description", ""),
                        "points": criterion_data.get("points", 0.0),
                        "criterion_use_range": criterion_data.get(
                            "criterion_use_range", False
                        ),
                    },
                )

                # Save ratings for this criterion
                for rating_data in criterion_data.get("ratings", []):
                    CanvasRubricRating.objects.update_or_create(
                        criterion=criterion,
                        canvas_id=rating_data["id"],
                        defaults={
                            "description": rating_data.get("description", ""),
                            "long_description": rating_data.get("long_description", ""),
                            "points": rating_data.get("points", 0.0),
                        },
                    )

        return assignment

    @sync_to_async
    def _save_submission(
        self, submission_data: Dict, assignment: CanvasAssignment
    ) -> Optional[CanvasSubmission]:
        """Save submission data to the database (sync function)"""
        # Find the enrollment
        try:
            enrollment = CanvasEnrollment.objects.get(
                course=assignment.course, user_id=submission_data["user_id"]
            )
        except CanvasEnrollment.DoesNotExist:
            logger.warning(
                f"Enrollment not found for user {submission_data['user_id']} in course {assignment.course.canvas_id}"
            )
            return None

        # Ensure excused field is always defined with a default value if not in submission_data
        excused = submission_data.get("excused")
        if excused is None:
            excused = False

        submission, created = CanvasSubmission.objects.update_or_create(
            canvas_id=submission_data["id"],
            assignment=assignment,
            enrollment=enrollment,
            defaults={
                "submitted_at": (
                    datetime.fromisoformat(
                        submission_data["submitted_at"].replace("Z", "+00:00")
                    )
                    if submission_data.get("submitted_at")
                    else None
                ),
                "grade": submission_data.get("grade"),
                "score": submission_data.get("score"),
                "workflow_state": submission_data.get("workflow_state", "unsubmitted"),
                "late": submission_data.get("late", False),
                "excused": excused,  # Use the variable we explicitly set
                "missing": submission_data.get("missing", False),
                "submission_type": submission_data.get("submission_type"),
                "url": submission_data.get("url"),
                "body": submission_data.get("body"),
            },
        )
        return submission

    async def sync_course(self, course_id: int, user_id: int = None) -> CanvasCourse:
        """
        Sync a course and its enrollments, assignments, and submissions

        Args:
            course_id: Canvas course ID
            user_id: ID of the user initiating the sync (for progress tracking)
        """
        # Initialize progress tracking if user_id is provided
        from .progress import SyncProgress

        if user_id:
            await SyncProgress.async_start_sync(user_id, course_id, total_steps=10)

        try:
            # Step 1: Get course data
            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    course_id,
                    current=1,
                    total=10,
                    status=SyncProgress.STATUS_FETCHING_COURSE,
                    message="Fetching course information from Canvas API...",
                )
            course_data = await self.get_course(course_id)

            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    course_id,
                    current=2,
                    total=10,
                    status=SyncProgress.STATUS_SAVING_DATA,
                    message="Saving course information to database...",
                )
            course = await self._save_course(course_data)

            # Step 2: Get enrollments data
            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    course_id,
                    current=3,
                    total=10,
                    status=SyncProgress.STATUS_FETCHING_ENROLLMENTS,
                    message="Fetching enrollment data from Canvas API...",
                )
            enrollments_data = await self.get_enrollments(course_id)

            # Step 3: Get all users with emails
            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    course_id,
                    current=4,
                    total=10,
                    status=SyncProgress.STATUS_FETCHING_USERS,
                    message="Fetching user details and email addresses...",
                )
            users_data = await self.get_course_users(course_id)

            # Create a lookup dictionary for user emails by user_id
            user_emails = {}
            for user in users_data:
                if "id" in user and "email" in user:
                    user_emails[user["id"]] = user["email"]

            # Step 4: Save enrollment data
            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    course_id,
                    current=5,
                    total=10,
                    status=SyncProgress.STATUS_SAVING_DATA,
                    message=f"Saving {len(enrollments_data)} enrollments to database...",
                )

            # Process enrollments with emails from the user data
            enrollment_count = len(enrollments_data)
            for i, enrollment_data in enumerate(enrollments_data):
                # Update progress for large enrollment sets
                if user_id and i > 0 and i % 25 == 0 and enrollment_count > 50:
                    await SyncProgress.async_update(
                        user_id,
                        course_id,
                        current=5,
                        total=10,
                        status=SyncProgress.STATUS_SAVING_DATA,
                        message=f"Saving enrollment {i} of {enrollment_count}...",
                    )

                # Try to add email from our lookup for any enrollment type
                if (
                    "user_id" in enrollment_data
                    and enrollment_data["user_id"] in user_emails
                ):

                    # Make sure there's a user dict
                    if "user" not in enrollment_data:
                        enrollment_data["user"] = {}

                    # Add email from our lookup
                    enrollment_data["user"]["email"] = user_emails[
                        enrollment_data["user_id"]
                    ]

                # Save the enrollment with the updated data
                await self._save_enrollment(enrollment_data, course)

            # Step 5: Get assignment data
            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    course_id,
                    current=6,
                    total=10,
                    status=SyncProgress.STATUS_FETCHING_ASSIGNMENTS,
                    message="Fetching assignments from Canvas API...",
                )
            assignments_data = await self.get_assignments(course_id)
            assignment_count = len(assignments_data)

            # Step 6: Process and save assignments
            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    course_id,
                    current=7,
                    total=10,
                    status=SyncProgress.STATUS_SAVING_DATA,
                    message=f"Saving {assignment_count} assignments to database...",
                )

            # Step 7: Process submissions for each assignment
            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    course_id,
                    current=8,
                    total=10,
                    status=SyncProgress.STATUS_PROCESSING_SUBMISSIONS,
                    message=f"Processing submissions for {assignment_count} assignments...",
                )

            for i, assignment_data in enumerate(assignments_data):
                # Save the assignment
                assignment = await self._save_assignment(assignment_data, course)

                # Update progress on a per-assignment basis
                if user_id and assignment_count > 0:
                    percentage_complete = (i / assignment_count) * 100
                    await SyncProgress.async_update(
                        user_id,
                        course_id,
                        current=8 + (i / assignment_count),
                        total=10,
                        status=SyncProgress.STATUS_PROCESSING_SUBMISSIONS,
                        message=f"Processing assignment {i+1} of {assignment_count} ({percentage_complete:.0f}%)...",
                    )

                # Get submissions for this assignment
                if user_id:
                    await SyncProgress.async_update(
                        user_id,
                        course_id,
                        current=8 + (i / assignment_count),
                        total=10,
                        status=SyncProgress.STATUS_FETCHING_SUBMISSIONS,
                        message=f"Fetching submissions for assignment '{assignment_data['name']}'...",
                    )

                submissions_data = await self.get_submissions(
                    course_id, assignment_data["id"]
                )

                # Save submissions
                if user_id and len(submissions_data) > 0:
                    await SyncProgress.async_update(
                        user_id,
                        course_id,
                        current=8 + (i / assignment_count),
                        total=10,
                        status=SyncProgress.STATUS_SAVING_DATA,
                        message=f"Saving {len(submissions_data)} submissions for assignment '{assignment_data['name']}'...",
                    )

                for submission_data in submissions_data:
                    await self._save_submission(submission_data, assignment)

            # Step 8: Sync Canvas groups and teams
            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    course_id,
                    current=9,
                    total=10,
                    status="syncing_groups",
                    message="Syncing Canvas groups and team memberships...",
                )

            try:
                # Import and use CanvasSyncer
                from .syncer import CanvasSyncer

                syncer = CanvasSyncer(self)

                # Log that we're starting group sync
                logger.info(
                    f"Starting group sync for course {course.name} (ID: {course.canvas_id})"
                )

                # Sync Canvas groups to teams and get current group IDs
                current_group_ids = await syncer.sync_canvas_groups(course, user_id)
                logger.info(
                    f"Synced {len(current_group_ids)} groups for course {course.name}"
                )

                # Sync group memberships to Student.team assignments
                await syncer.sync_group_memberships(course, user_id)
                logger.info(f"Synced group memberships for course {course.name}")

                # Optional: Clean up teams no longer in Canvas
                # (This is commented out by default as it could remove manually created teams)
                # await Team.objects.filter(
                #    canvas_course=course,
                #    canvas_group_id__isnull=False
                # ).exclude(canvas_group_id__in=current_group_ids).adelete()
            except Exception as e:
                logger.error(f"Error syncing Canvas groups: {e}")
                # We'll log the error but continue with the rest of the sync process
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")

            # Update last sync timestamp
            from django.utils import timezone

            self.integration.last_sync = timezone.now()
            await sync_to_async(self.integration.save)()

            # Mark sync as complete
            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    course_id,
                    current=9.5,
                    total=10,
                    status=SyncProgress.STATUS_SAVING_DATA,
                    message="Finalizing sync and updating timestamps...",
                )

                # Small delay to ensure the UI gets updated before completion
                import asyncio

                await asyncio.sleep(0.5)

                await SyncProgress.async_complete_sync(
                    user_id,
                    course_id,
                    success=True,
                    message=f"Successfully synced {course.name} with {len(enrollments_data)} enrollments and {assignment_count} assignments",
                )

            return course

        except Exception as e:
            # Mark sync as failed if there was an error
            if user_id:
                # Get a friendlier error message depending on error type
                error_message = str(e)
                friendly_message = "Sync failed with an error."

                if "401" in error_message or "invalid_grant" in error_message:
                    friendly_message = "Authentication failed. Your Canvas API key may be invalid or expired."
                elif "404" in error_message:
                    friendly_message = "Resource not found. The course ID may be invalid or you don't have access."
                elif "429" in error_message:
                    friendly_message = "Rate limit exceeded. Canvas API limits were reached. Please try again later."
                elif "500" in error_message:
                    friendly_message = (
                        "Canvas API server error. Please try again later."
                    )
                elif "Connection" in error_message:
                    friendly_message = "Connection error. Please check your internet connection and try again."

                await SyncProgress.async_complete_sync(
                    user_id,
                    course_id,
                    success=False,
                    message=friendly_message,
                    error=error_message,
                )
            raise

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

    @sync_to_async
    def _save_group_category(self, category_data: Dict, course: CanvasCourse):
        """Save group category data to the database (sync function)"""
        from .models import CanvasGroupCategory

        category, created = CanvasGroupCategory.objects.update_or_create(
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

    @sync_to_async
    def _save_group(self, group_data: Dict, category):
        """Save group data to the database (sync function)"""
        from .models import CanvasGroup
        from django.utils import timezone

        # Safely handle description which might be None
        description = group_data.get("description", "")
        if description is None:
            description = ""

        group, created = CanvasGroup.objects.update_or_create(
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
                "last_synced_at": timezone.now(),
            },
        )
        return group

    @sync_to_async
    def _save_group_membership(self, member_data: Dict, group):
        """Save group membership data to the database (sync function)"""
        from .models import CanvasGroupMembership, CanvasEnrollment
        from core.models import Student
        import logging

        logger = logging.getLogger(__name__)

        # Try to find matching student - first by canvas_user_id
        student = None
        if "id" in member_data:
            try:
                # First try exact match by canvas_user_id
                student = Student.objects.filter(
                    canvas_user_id=str(member_data["id"])
                ).first()

                # If student not found, try to find by enrollment
                if student is None:
                    # Look for enrollment with this user_id to find a linked student
                    enrollment = CanvasEnrollment.objects.filter(
                        user_id=member_data["id"], course=group.category.course
                    ).first()

                    if enrollment and enrollment.student:
                        student = enrollment.student
                        # Update the student's canvas_user_id for future lookups
                        if not student.canvas_user_id:
                            student.canvas_user_id = str(member_data["id"])
                            student.save(update_fields=["canvas_user_id"])
                            logger.info(
                                f"Updated student {student.full_name} with Canvas user ID {member_data['id']}"
                            )

                # If still not found, look by email as a last resort
                if student is None and member_data.get("email"):
                    student = Student.objects.filter(email=member_data["email"]).first()
                    if student:
                        # Update the student's canvas_user_id
                        student.canvas_user_id = str(member_data["id"])
                        student.save(update_fields=["canvas_user_id"])
                        logger.info(
                            f"Matched student {student.full_name} by email with Canvas user ID {member_data['id']}"
                        )

            except Exception as e:
                logger.error(
                    f"Error finding student for member {member_data.get('name')}: {str(e)}"
                )

        membership, created = CanvasGroupMembership.objects.update_or_create(
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

    async def sync_all_courses(self, user_id: int = None) -> List[CanvasCourse]:
        """
        Sync all available courses

        Args:
            user_id: ID of the user initiating the sync (for progress tracking)
        """
        from .progress import SyncProgress

        try:
            # Step 1: Get available courses from Canvas API
            if user_id:
                await SyncProgress.async_start_sync(
                    user_id, total_steps=100  # Will be adjusted based on course count
                )
                await SyncProgress.async_update(
                    user_id,
                    current=1,
                    total=100,
                    status=SyncProgress.STATUS_FETCHING_COURSE,
                    message="Fetching available courses from Canvas API...",
                )

            courses_data = await self.get_courses()
            synced_courses = []

            if not courses_data:
                if user_id:
                    await SyncProgress.async_complete_sync(
                        user_id, success=True, message="No courses found to sync."
                    )
                return []

            # Update progress based on course count
            course_count = len(courses_data)
            progress_per_course = 95 / max(
                course_count, 1
            )  # 95% of progress for courses, 5% for setup/cleanup

            # Update progress to show found courses
            if user_id:
                await SyncProgress.async_update(
                    user_id,
                    current=5,
                    total=100,
                    status=SyncProgress.STATUS_PENDING,
                    message=f"Found {course_count} courses to sync",
                )

            # Sync each course
            errors = []
            for i, course_data in enumerate(courses_data):
                course_name = course_data.get(
                    "name", f"Course {course_data.get('id', 'unknown')}"
                )
                progress_start = 5 + (i * progress_per_course)

                try:
                    # Update progress at the overall level
                    if user_id:
                        await SyncProgress.async_update(
                            user_id,
                            current=progress_start,
                            total=100,
                            status="syncing_course",
                            message=f"Syncing course {i+1} of {course_count}: {course_name}",
                        )

                    # Sync the individual course (this will track its own progress if user_id is provided)
                    # Note: we pass None for the user_id to avoid nested progress tracking
                    # We'll handle all progress tracking here for the overall process
                    course = await self.sync_course(course_data["id"], None)
                    synced_courses.append(course)

                    # Update progress after successfully syncing this course
                    if user_id:
                        percentage = int((i + 1) / course_count * 100)
                        await SyncProgress.async_update(
                            user_id,
                            current=progress_start + progress_per_course,
                            total=100,
                            status=SyncProgress.STATUS_COMPLETED,
                            message=f"Completed course {i+1} of {course_count}: {course_name} ({percentage}% complete)",
                        )

                except Exception as e:
                    errors.append({"course": course_name, "error": str(e)})
                    logger.error(f"Error syncing course {course_data.get('id')}: {e}")

                    # Update progress to show error for this course
                    if user_id:
                        await SyncProgress.async_update(
                            user_id,
                            current=progress_start + progress_per_course,
                            total=100,
                            status=SyncProgress.STATUS_ERROR,
                            message=f"Error syncing course {i+1} of {course_count}: {course_name}",
                        )

            # Mark the overall sync as complete
            if user_id:
                success_message = (
                    f"Successfully synced {len(synced_courses)} out of {course_count} courses. "
                    f"{len(errors)} courses had errors."
                )

                # Add more detail if there were errors
                error_detail = None
                if errors:
                    error_courses = ", ".join([e["course"] for e in errors[:3]])
                    if len(errors) > 3:
                        error_courses += f", and {len(errors) - 3} more"
                    error_detail = f"Errors in courses: {error_courses}"

                await SyncProgress.async_complete_sync(
                    user_id,
                    success=len(synced_courses) > 0,
                    message=success_message,
                    error=error_detail,
                )

            return synced_courses

        except Exception as e:
            # Handle any overall errors
            if user_id:
                error_message = str(e)
                friendly_message = "Failed to sync courses."

                if "401" in error_message:
                    friendly_message = "Authentication failed. Your Canvas API key may be invalid or expired."
                elif "Connection" in error_message:
                    friendly_message = (
                        "Connection error. Please check your internet connection."
                    )

                await SyncProgress.async_complete_sync(
                    user_id,
                    success=False,
                    message=friendly_message,
                    error=error_message,
                )

            logger.error(f"Error in sync_all_courses: {e}")
            raise
