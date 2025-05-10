"""
Canvas Syncer - Handles synchronization of Canvas data to GradeBench models
"""
import logging
from typing import Dict, List, Optional, Tuple, Union

from asgiref.sync import sync_to_async
from django.utils import timezone

from lms.canvas.client import Client
from lms.canvas.models import CanvasCourse, CanvasEnrollment
from core.models import Student, Team

logger = logging.getLogger(__name__)


class CanvasSyncer:
    """
    Service for syncing Canvas data to GradeBench models. This class handles
    the logic for synchronizing courses, enrollments, assignments, submissions,
    and groups from Canvas to the local database.
    """

    def __init__(self, client: Client):
        """Initialize with a Canvas API client"""
        self.client = client

    async def sync_course(self, course_id: int, user_id: int = None) -> CanvasCourse:
        """
        Sync a course and its data from Canvas
        
        Args:
            course_id: Canvas course ID
            user_id: ID of the user initiating the sync (for progress tracking)
        """
        from .progress import SyncProgress
        
        # Initialize progress tracking if user_id is provided
        if user_id:
            await SyncProgress.async_start_sync(user_id, course_id, total_steps=12)  # Increased for group sync
            
        try:
            # Step 1: Get course data
            if user_id:
                await SyncProgress.async_update(
                    user_id, course_id, current=1, total=12, 
                    status=SyncProgress.STATUS_FETCHING_COURSE,
                    message="Fetching course information from Canvas API..."
                )
            course_data = await self.client.get_course(course_id)
            
            if user_id:
                await SyncProgress.async_update(
                    user_id, course_id, current=2, total=12, 
                    status=SyncProgress.STATUS_SAVING_DATA,
                    message="Saving course information to database..."
                )
            course = await self.client._save_course(course_data)

            # Step 2: Get enrollments data
            if user_id:
                await SyncProgress.async_update(
                    user_id, course_id, current=3, total=12, 
                    status=SyncProgress.STATUS_FETCHING_ENROLLMENTS,
                    message="Fetching enrollment data from Canvas API..."
                )
            enrollments_data = await self.client.get_enrollments(course_id)
            
            # Step 3: Get all users with emails
            if user_id:
                await SyncProgress.async_update(
                    user_id, course_id, current=4, total=12, 
                    status=SyncProgress.STATUS_FETCHING_USERS,
                    message="Fetching user details and email addresses..."
                )
            users_data = await self.client.get_course_users(course_id)
            
            # Create a lookup dictionary for user emails by user_id
            user_emails = {}
            for user in users_data:
                if 'id' in user and 'email' in user:
                    user_emails[user['id']] = user['email']
            
            # Step 4: Save enrollment data
            if user_id:
                await SyncProgress.async_update(
                    user_id, course_id, current=5, total=12, 
                    status=SyncProgress.STATUS_SAVING_DATA,
                    message=f"Saving {len(enrollments_data)} enrollments to database..."
                )
                
            # Process enrollments with emails from the user data
            enrollment_count = len(enrollments_data)
            for i, enrollment_data in enumerate(enrollments_data):
                # Update progress for large enrollment sets
                if user_id and i > 0 and i % 25 == 0 and enrollment_count > 50:
                    await SyncProgress.async_update(
                        user_id, course_id, current=5, total=12,
                        status=SyncProgress.STATUS_SAVING_DATA,
                        message=f"Saving enrollment {i} of {enrollment_count}..."
                    )

                # Try to add email from our lookup for any enrollment type
                if ('user_id' in enrollment_data and
                    enrollment_data['user_id'] in user_emails):

                    # Make sure there's a user dict
                    if 'user' not in enrollment_data:
                        enrollment_data['user'] = {}

                    # Add email from our lookup
                    enrollment_data['user']['email'] = user_emails[enrollment_data['user_id']]

                # Save the enrollment with the updated data
                enrollment = await self.client._save_enrollment(enrollment_data, course)

            # Create Student records for all student enrollments
            if user_id:
                await SyncProgress.async_update(
                    user_id, course_id, current=5.5, total=12,
                    status="creating_students",
                    message="Creating Student records from enrollments..."
                )

            # Get all student enrollments
            student_enrollments = await self._get_student_enrollments(course)

            # Create Student records for each enrollment if needed
            student_count = 0
            for enrollment in student_enrollments:
                try:
                    student = await self._get_or_create_student(enrollment)
                    if student:
                        student_count += 1

                        # If student has a Canvas group membership, set team
                        # This is a basic setup that will be enhanced later during group membership sync
                        # We do this in case there are students who are in Canvas groups but the group sync fails
                        await self._try_assign_group_to_student(student, enrollment, course)
                except Exception as e:
                    logger.error(f"Error creating student from enrollment {enrollment.id}: {str(e)}")

            if user_id:
                await SyncProgress.async_update(
                    user_id, course_id, current=5.8, total=12,
                    status=SyncProgress.STATUS_SAVING_DATA,
                    message=f"Created/updated {student_count} Student records"
                )

            # Step 5: Get assignment data
            if user_id:
                await SyncProgress.async_update(
                    user_id, course_id, current=6, total=12, 
                    status=SyncProgress.STATUS_FETCHING_ASSIGNMENTS,
                    message="Fetching assignments from Canvas API..."
                )
            assignments_data = await self.client.get_assignments(course_id)
            assignment_count = len(assignments_data)
            
            # Step 6: Process and save assignments
            if user_id:
                await SyncProgress.async_update(
                    user_id, course_id, current=7, total=12, 
                    status=SyncProgress.STATUS_SAVING_DATA,
                    message=f"Saving {assignment_count} assignments to database..."
                )
            
            # Step 7: Process submissions for each assignment
            if user_id:
                await SyncProgress.async_update(
                    user_id, course_id, current=8, total=12, 
                    status=SyncProgress.STATUS_PROCESSING_SUBMISSIONS,
                    message=f"Processing submissions for {assignment_count} assignments..."
                )
                
            for i, assignment_data in enumerate(assignments_data):
                # Save the assignment
                assignment = await self.client._save_assignment(assignment_data, course)
                
                # Update progress on a per-assignment basis
                if user_id and assignment_count > 0:
                    percentage_complete = (i / assignment_count) * 100
                    await SyncProgress.async_update(
                        user_id, course_id, 
                        current=8 + (i / assignment_count),
                        total=12,
                        status=SyncProgress.STATUS_PROCESSING_SUBMISSIONS,
                        message=f"Processing assignment {i+1} of {assignment_count} ({percentage_complete:.0f}%)..."
                    )

                # Get submissions for this assignment
                if user_id:
                    await SyncProgress.async_update(
                        user_id, course_id,
                        current=8 + (i / assignment_count),
                        total=12,
                        status=SyncProgress.STATUS_FETCHING_SUBMISSIONS,
                        message=f"Fetching submissions for assignment '{assignment_data['name']}'..."
                    )
                    
                submissions_data = await self.client.get_submissions(course_id, assignment_data['id'])
                
                # Save submissions
                if user_id and len(submissions_data) > 0:
                    await SyncProgress.async_update(
                        user_id, course_id,
                        current=8 + (i / assignment_count),
                        total=12,
                        status=SyncProgress.STATUS_SAVING_DATA,
                        message=f"Saving {len(submissions_data)} submissions for assignment '{assignment_data['name']}'..."
                    )
                
                for submission_data in submissions_data:
                    await self.client._save_submission(submission_data, assignment)

            # Step 8: Sync Canvas groups
            if user_id:
                await SyncProgress.async_update(
                    user_id, course_id, current=10, total=12,
                    status="syncing_groups",
                    message="Syncing Canvas groups and team memberships..."
                )

            try:
                # Sync groups and get current group IDs for cleanup
                current_group_ids = await self.sync_canvas_groups(course, user_id)

                # Only try to sync memberships if we found groups
                if current_group_ids:
                    await self.sync_group_memberships(course, user_id)
                else:
                    if user_id:
                        await SyncProgress.async_update(
                            user_id, course_id,
                            current=10.5, total=12,
                            status="info",
                            message="No Canvas groups found, skipping membership sync."
                        )
                    logger.info(f"No Canvas groups found for course {course.name}, skipping membership sync")
            except Exception as e:
                # Log the error but continue with sync (don't fail the whole sync process)
                logger.error(f"Error syncing groups for course {course_id}: {str(e)}")
                if user_id:
                    await SyncProgress.async_update(
                        user_id, course_id,
                        current=10.5, total=12,
                        status="warning",
                        message=f"Warning: Error syncing Canvas groups: {str(e)}"
                    )

            # Update last sync timestamp
            from django.utils import timezone
            self.client.integration.last_sync = timezone.now()
            await sync_to_async(self.client.integration.save)()
            
            # Mark sync as complete
            if user_id:
                await SyncProgress.async_update(
                    user_id, course_id, 
                    current=11.5, 
                    total=12,
                    status=SyncProgress.STATUS_SAVING_DATA,
                    message="Finalizing sync and updating timestamps..."
                )
                
                # Small delay to ensure the UI gets updated before completion
                import asyncio
                await asyncio.sleep(0.5)
                
                await SyncProgress.async_complete_sync(
                    user_id, course_id, 
                    success=True,
                    message=f"Successfully synced {course.name} with {len(enrollments_data)} enrollments, {assignment_count} assignments, and {len(current_group_ids)} groups"
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
                    friendly_message = "Canvas API server error. Please try again later."
                elif "Connection" in error_message:
                    friendly_message = "Connection error. Please check your internet connection and try again."
                
                await SyncProgress.async_complete_sync(
                    user_id, course_id, 
                    success=False,
                    message=friendly_message,
                    error=error_message
                )
            
            logger.error(f"Error syncing course {course_id}: {str(e)}")
            raise

    async def sync_canvas_groups(self, course: CanvasCourse, user_id=None) -> List[int]:
        """
        Sync Canvas groups for a course to Teams

        Args:
            course: The Canvas course to sync groups for
            user_id: ID of the user initiating the sync (for progress tracking)

        Returns:
            List of current Canvas group IDs that were synced
        """
        from .progress import SyncProgress

        if user_id:
            await SyncProgress.async_update(
                user_id, course.canvas_id,
                status="fetching_groups",
                message="Fetching group categories from Canvas..."
            )

        # 1. Fetch group‑sets
        try:
            categories = await self.client.get_group_categories(course.canvas_id)

            # Handle case where API returns None or empty list
            if not categories:
                if user_id:
                    await SyncProgress.async_update(
                        user_id, course.canvas_id,
                        status="info",
                        message="No Canvas group categories found for this course."
                    )
                logger.info(f"No group categories found for course {course.name} (ID: {course.canvas_id})")
                return []

        except Exception as e:
            logger.error(f"Error fetching group categories for course {course.canvas_id}: {str(e)}")
            if user_id:
                await SyncProgress.async_update(
                    user_id, course.canvas_id,
                    status="warning",
                    message=f"Error fetching Canvas groups: {str(e)}"
                )
            return []

        # Track all Canvas group IDs to handle cleanup later
        current_group_ids = []

        # 2. Upsert Teams for each Canvas group
        for cat in categories:
            # Skip if category data is missing
            if not cat or 'id' not in cat:
                continue

            cat_name = cat.get('name', 'Unnamed Category')

            if user_id:
                await SyncProgress.async_update(
                    user_id, course.canvas_id,
                    status="fetching_groups",
                    message=f"Fetching groups in category: {cat_name}"
                )

            try:
                # Get groups for this category
                groups = await self.client.get_groups(cat['id'])

                # Handle case where API returns None or empty list
                if not groups:
                    logger.info(f"No groups found in category '{cat_name}' for course {course.name}")
                    continue

                if user_id and groups:
                    await SyncProgress.async_update(
                        user_id, course.canvas_id,
                        status="saving_groups",
                        message=f"Saving {len(groups)} groups to database..."
                    )

                for grp in groups:
                    # Skip if group data is missing
                    if not grp or 'id' not in grp:
                        continue

                    current_group_ids.append(grp['id'])

                    # Perform update_or_create with sync_to_async
                    await self._save_team(
                        canvas_group_id=grp['id'],
                        canvas_course=course,
                        name=grp.get('name', '')[:100],
                        description=grp.get('description', '')[:500]
                    )
            except Exception as e:
                logger.error(f"Error processing group category '{cat_name}' for course {course.canvas_id}: {str(e)}")
                continue

        # Log group count
        logger.info(f"Synced {len(current_group_ids)} Canvas groups for course {course.name} (ID: {course.canvas_id})")

        # Return group IDs for potential cleanup
        return current_group_ids

    @sync_to_async
    def _save_team(self, canvas_group_id: int, canvas_course: CanvasCourse,
                  name: str, description: str) -> Tuple[Team, bool]:
        """Save or update a Team from Canvas group data (sync function)"""
        try:
            # Ensure parameters are valid
            if not canvas_group_id or not canvas_course:
                logger.error(f"Invalid parameters for _save_team: group_id={canvas_group_id}, course={canvas_course}")
                return None, False

            # Clean and validate inputs
            team_name = str(name).strip()[:100] if name else f"Team {canvas_group_id}"
            team_desc = str(description).strip()[:500] if description else ""

            # Create or update the team
            team, created = Team.objects.update_or_create(
                canvas_group_id=canvas_group_id,
                canvas_course=canvas_course,
                defaults={
                    'name': team_name,
                    'description': team_desc,
                    'last_synced_at': timezone.now()
                }
            )

            # Log when teams are created or updated
            if created:
                logger.info(f"Created new team from Canvas group: {team.name} (ID: {canvas_group_id})")
            else:
                logger.info(f"Updated existing team from Canvas group: {team.name} (ID: {canvas_group_id})")

            return team, created

        except Exception as e:
            logger.error(f"Error saving team for Canvas group {canvas_group_id}: {str(e)}")
            return None, False

    async def sync_group_memberships(self, course: CanvasCourse, user_id=None):
        """
        Sync group memberships to Student.team assignments

        Args:
            course: The Canvas course to sync memberships for
            user_id: ID of the user initiating the sync (for progress tracking)
        """
        from .progress import SyncProgress

        # Get teams with canvas_group_id
        teams = await self._get_canvas_teams(course)

        # Handle case where there are no Canvas teams
        if not teams:
            if user_id:
                await SyncProgress.async_update(
                    user_id, course.canvas_id,
                    status="info",
                    message="No Canvas teams found to sync memberships."
                )
            logger.info(f"No Canvas teams found to sync memberships for course {course.name} (ID: {course.canvas_id})")
            return

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
                # Get group members
                members = await self.client.get_group_members(team.canvas_group_id)

                # Handle case where API returns None or empty list
                if not members:
                    logger.info(f"No members found for team {team.name} (Canvas group ID: {team.canvas_group_id})")
                    continue

                for m in members:
                    # Skip if member data is missing
                    if not m or 'id' not in m:
                        continue

                    try:
                        # Get the enrollment - the 'id' in the member response is the Canvas user_id
                        enrollment = await self._get_enrollment_by_user_id(m['id'], course)
                        if not enrollment:
                            logger.warning(
                                f"Enrollment not found for user ID {m['id']} in team {team.name}"
                            )
                            continue

                        # Get or create student
                        student = await self._get_or_create_student(enrollment)
                        if not student:
                            continue

                        # Assign team to student if different
                        if student.team != team:
                            old_team = student.team
                            student.team = team
                            await sync_to_async(student.save)(update_fields=['team'])

                            logger.info(
                                f"Updated student {student.full_name} team assignment: " +
                                f"{old_team.name if old_team else 'None'} → {team.name}"
                            )

                    except Exception as e:
                        logger.error(f"Error processing member {m.get('id', 'unknown')} for team {team.name}: {str(e)}")
                        continue

            except Exception as e:
                logger.error(f"Error syncing memberships for team {team.name}: {str(e)}")
                continue

        logger.info(f"Finished syncing memberships for {len(teams)} teams in course {course.name} (ID: {course.canvas_id})")

    @sync_to_async
    def _get_canvas_teams(self, course: CanvasCourse) -> List[Team]:
        """Get all Canvas teams for a course (sync function)"""
        return list(Team.objects.filter(canvas_course=course, canvas_group_id__isnull=False))

    @sync_to_async
    def _get_student_enrollments(self, course: CanvasCourse) -> List[CanvasEnrollment]:
        """Get all student enrollments for a course (sync function)"""
        return list(CanvasEnrollment.objects.filter(
            course=course,
            role='StudentEnrollment',
            enrollment_state='active'
        ))

    @sync_to_async
    def _get_enrollment(self, canvas_id: int, course: CanvasCourse) -> Optional[CanvasEnrollment]:
        """Get a Canvas enrollment by canvas_id (sync function)"""
        try:
            return CanvasEnrollment.objects.get(canvas_id=canvas_id, course=course)
        except CanvasEnrollment.DoesNotExist:
            return None

    @sync_to_async
    def _get_enrollment_by_user_id(self, user_id: int, course: CanvasCourse) -> Optional[CanvasEnrollment]:
        """Get a Canvas enrollment by user_id (sync function)"""
        try:
            return CanvasEnrollment.objects.get(user_id=user_id, course=course)
        except CanvasEnrollment.DoesNotExist:
            return None
            
    @sync_to_async
    def _get_or_create_student(self, enrollment: CanvasEnrollment) -> Optional[Student]:
        """Get or create a Student from an enrollment (sync function)"""
        # Use existing student if already linked
        if enrollment.student:
            return enrollment.student

        # Create new student
        try:
            user_name_parts = enrollment.user_name.split()
            first_name = user_name_parts[0] if user_name_parts else "Unknown"
            last_name = " ".join(user_name_parts[1:]) if len(user_name_parts) > 1 else ""

            student, created = Student.objects.update_or_create(
                canvas_user_id=str(enrollment.user_id),
                defaults={
                    'email': enrollment.email or f"canvas-user-{enrollment.user_id}@example.com",
                    'first_name': first_name,
                    'last_name': last_name,
                }
            )

            if created:
                logger.info(f"Created new student from Canvas enrollment: {student.full_name}")

            # Link student to enrollment
            enrollment.student = student
            enrollment.save(update_fields=['student'])

            return student

        except Exception as e:
            logger.error(f"Error creating student for enrollment {enrollment.id}: {str(e)}")
            return None

    async def _try_assign_group_to_student(self, student: Student, enrollment: CanvasEnrollment, course: CanvasCourse):
        """Try to find and assign a Canvas group to a student"""
        try:
            # Skip if student already has a team
            if student.team is not None:
                return

            # Get Canvas teams for this course
            teams = await self._get_canvas_teams(course)
            if not teams:
                return

            # For each team, check group members
            for team in teams:
                if not team.canvas_group_id:
                    continue

                members = await self.client.get_group_members(team.canvas_group_id)

                # Check if student is in this group
                for member in members:
                    if member.get('id') == enrollment.user_id:  # Compare with user_id, not canvas_id
                        # Found a match - assign team to student
                        student.team = team
                        await sync_to_async(student.save)(update_fields=['team'])
                        logger.info(f"Assigned student {student.full_name} to team {team.name} from Canvas group")
                        return

        except Exception as e:
            logger.error(f"Error trying to assign group to student {student.full_name}: {str(e)}")
            # Don't raise - just log the error and continue

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
                    user_id, current=1, total=100,
                    status=SyncProgress.STATUS_FETCHING_COURSE,
                    message="Fetching available courses from Canvas API..."
                )
                
            courses_data = await self.client.get_courses()
            synced_courses = []
            
            if not courses_data:
                if user_id:
                    await SyncProgress.async_complete_sync(
                        user_id,
                        success=True,
                        message="No courses found to sync."
                    )
                return []
            
            # Update progress based on course count
            course_count = len(courses_data)
            progress_per_course = 95 / max(course_count, 1)  # 95% of progress for courses, 5% for setup/cleanup
            
            # Update progress to show found courses
            if user_id:
                await SyncProgress.async_update(
                    user_id, current=5, total=100,
                    status=SyncProgress.STATUS_PENDING,
                    message=f"Found {course_count} courses to sync"
                )
    
            # Sync each course
            errors = []
            for i, course_data in enumerate(courses_data):
                course_name = course_data.get('name', f"Course {course_data.get('id', 'unknown')}")
                progress_start = 5 + (i * progress_per_course)
                
                try:
                    # Update progress at the overall level
                    if user_id:
                        await SyncProgress.async_update(
                            user_id, 
                            current=progress_start, 
                            total=100,
                            status="syncing_course",
                            message=f"Syncing course {i+1} of {course_count}: {course_name}"
                        )
                    
                    # Sync the individual course (this will track its own progress if user_id is provided)
                    # Note: we pass None for the user_id to avoid nested progress tracking
                    # We'll handle all progress tracking here for the overall process
                    course = await self.sync_course(course_data['id'], None)
                    synced_courses.append(course)
                    
                    # Update progress after successfully syncing this course
                    if user_id:
                        percentage = int((i + 1) / course_count * 100)
                        await SyncProgress.async_update(
                            user_id, 
                            current=progress_start + progress_per_course, 
                            total=100,
                            status=SyncProgress.STATUS_COMPLETED,
                            message=f"Completed course {i+1} of {course_count}: {course_name} ({percentage}% complete)"
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
                            message=f"Error syncing course {i+1} of {course_count}: {course_name}"
                        )
                    
            # Mark the overall sync as complete
            if user_id:
                success_message = (f"Successfully synced {len(synced_courses)} out of {course_count} courses. "
                                  f"{len(errors)} courses had errors.")
                
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
                    error=error_detail
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
                    friendly_message = "Connection error. Please check your internet connection."
                
                await SyncProgress.async_complete_sync(
                    user_id, 
                    success=False,
                    message=friendly_message,
                    error=error_message
                )
            
            logger.error(f"Error in sync_all_courses: {e}")
            raise