# lms/canvas/mixins/sync_mixin.py
"""
Mixin providing synchronization orchestration methods for Canvas API client.
Properly integrated with cache-based progress tracking.
"""
import asyncio
import logging
import traceback
from typing import Dict, List, Optional, Any

# Import the progress class - use proper relative import
from ..progress import SyncProgress

logger = logging.getLogger(__name__)


class SyncMixin:
    """Provides synchronization orchestration methods with proper progress tracking"""

    async def sync_course(self, course_id: int, user_id: int = None) -> 'CanvasCourse':
        """
        Sync a course and its enrollments, assignments, and submissions

        Args:
            course_id: Canvas course ID
            user_id: ID of the user initiating the sync (for progress tracking)
        """
        try:
            # Initialize progress tracking if user_id is provided
            if user_id:
                logger.info(
                    f"Starting course sync for user {user_id}, course {course_id}")
                await SyncProgress.async_start_sync(user_id, course_id, total_steps=10)

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
                from ..syncer import CanvasSyncer

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
                logger.info(
                    f"Synced group memberships for course {course.name}")

                # Optional: Clean up teams no longer in Canvas
                # (This is commented out by default as it could remove manually created teams)
                # await Team.objects.filter(
                #    canvas_course=course,
                #    canvas_group_id__isnull=False
                # ).exclude(canvas_group_id__in=current_group_ids).adelete()
            except Exception as e:
                logger.error(f"Error syncing Canvas groups: {e}")
                # We'll log the error but continue with the rest of the sync process
                logger.error(f"Traceback: {traceback.format_exc()}")

            # Update last sync timestamp
            self.integration.last_sync = self.timezone.now()
            await self.integration.asave()

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
                await asyncio.sleep(0.5)

                await SyncProgress.async_complete_sync(
                    user_id,
                    course_id,
                    success=True,
                    message=f"Successfully synced {course.name} with {len(enrollments_data)} enrollments and {assignment_count} assignments",
                )
                logger.info(
                    f"Successfully completed sync for course {course_id}")

            return course

        except Exception as e:
            # Log the full error with traceback
            logger.error(
                f"Error in sync_course for course_id={course_id}: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

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

                # Attempt to update the progress to show failure
                try:
                    await SyncProgress.async_complete_sync(
                        user_id,
                        course_id,
                        success=False,
                        message=friendly_message,
                        error=error_message,
                    )
                    logger.info(
                        f"Marked sync as failed for course {course_id}: {friendly_message}")
                except Exception as progress_error:
                    # If updating progress fails, log that too
                    logger.error(
                        f"Error updating progress for failed sync: {progress_error}")

            # Re-raise the exception to be handled by the caller
            raise

    async def sync_all_courses(self, user_id: int = None) -> List['CanvasCourse']:
        """
        Sync all available courses

        Args:
            user_id: ID of the user initiating the sync (for progress tracking)
        """
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
                    logger.error(
                        f"Error syncing course {course_data.get('id')}: {e}")
                    logger.error(f"Traceback: {traceback.format_exc()}")

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
                    error_courses = ", ".join(
                        [e["course"] for e in errors[:3]])
                    if len(errors) > 3:
                        error_courses += f", and {len(errors) - 3} more"
                    error_detail = f"Errors in courses: {error_courses}"

                await SyncProgress.async_complete_sync(
                    user_id,
                    success=len(synced_courses) > 0,
                    message=success_message,
                    error=error_detail,
                )
                logger.info(
                    f"Completed sync_all_courses with {len(synced_courses)} successes, {len(errors)} failures")

            return synced_courses

        except Exception as e:
            # Handle any overall errors
            logger.error(f"Error in sync_all_courses: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")

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

            raise
