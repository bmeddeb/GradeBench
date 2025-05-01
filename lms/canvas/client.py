# lms/canvas/client.py

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import httpx
from asgiref.sync import sync_to_async


from .models import (CanvasAssignment, CanvasCourse, CanvasEnrollment,
                     CanvasIntegration, CanvasRubric, CanvasRubricCriterion,
                     CanvasRubricRating, CanvasSubmission)

logger = logging.getLogger(__name__)


class Client:
    """Async client for interacting with the Canvas API"""

    def __init__(self, integration: CanvasIntegration):
        """Initialize with a CanvasIntegration instance"""
        self.integration = integration
        self.base_url = integration.canvas_url
        self.api_key = integration.api_key
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    async def request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Any:
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
                    json=data if method.lower() in ['post', 'put'] else None
                )
                response.raise_for_status()

                result = response.json()
                if isinstance(result, list) and 'link' in response.headers:
                    while 'next' in response.headers.get('link', ''):
                        links = response.headers.get('link').split(',')
                        next_url = None
                        for link in links:
                            if 'rel="next"' in link:
                                next_url = link.split(';')[0].strip('<> ')
                                break
                        if not next_url:
                            break
                        next_response = await client.get(next_url, headers=self.headers)
                        next_response.raise_for_status()
                        next_result = next_response.json()
                        result.extend(next_result)
                        if 'link' not in next_response.headers or 'next' not in next_response.headers.get('link', ''):
                            break
                return result
            except httpx.HTTPError as e:
                logger.error(f"API request error: {e}")
                raise

    async def get_courses(self) -> List[Dict]:
        """Get all courses for the authenticated user"""
        return await self.request('GET', 'courses', params={
            'include[]': ['term', 'total_students', 'syllabus_body', 'course_image'],
            'state[]': ['available', 'completed', 'unpublished'],
            'per_page': 100
        })

    async def get_course(self, course_id: int) -> Dict:
        """Get a single course by ID"""
        return await self.request('GET', f'courses/{course_id}', params={
            'include[]': ['term', 'syllabus_body', 'course_image']
        })

    async def get_enrollments(self, course_id: int) -> List[Dict]:
        """Get all enrollments for a course"""
        return await self.request('GET', f'courses/{course_id}/enrollments', params={
            'include[]': ['avatar_url', 'group_ids', 'locked', 'observed_users', 'can_be_removed', 'uuid', 'current_grading_period_scores', 'user'],
            'per_page': 100
        })

    async def get_assignments(self, course_id: int) -> List[Dict]:
        """Get all assignments for a course"""
        return await self.request('GET', f'courses/{course_id}/assignments', params={
            'include[]': ['submission', 'rubric', 'all_dates', 'overrides'],
            'per_page': 100
        })

    async def get_assignment(self, course_id: int, assignment_id: int) -> Dict:
        """Get a single assignment by ID"""
        return await self.request('GET', f'courses/{course_id}/assignments/{assignment_id}', params={
            'include[]': ['submission', 'rubric', 'all_dates', 'overrides']
        })

    async def get_submissions(self, course_id: int, assignment_id: int) -> List[Dict]:
        """Get all submissions for an assignment"""
        return await self.request('GET', f'courses/{course_id}/assignments/{assignment_id}/submissions', params={
            'include[]': ['user', 'submission_comments', 'rubric_assessment'],
            'per_page': 100
        })

    async def get_submission(self, course_id: int, assignment_id: int, user_id: int) -> Dict:
        """Get a submission for a specific user"""
        return await self.request('GET', f'courses/{course_id}/assignments/{assignment_id}/submissions/{user_id}', params={
            'include[]': ['user', 'submission_comments', 'rubric_assessment']
        })

    @sync_to_async
    def _save_course(self, course_data: Dict) -> CanvasCourse:
        """Save course data to the database (sync function)"""
        course, created = CanvasCourse.objects.update_or_create(
            canvas_id=course_data['id'],
            integration=self.integration,
            defaults={
                'name': course_data['name'],
                'course_code': course_data['course_code'],
                'start_at': datetime.fromisoformat(course_data['start_at'].replace('Z', '+00:00')) if course_data.get('start_at') else None,
                'end_at': datetime.fromisoformat(course_data['end_at'].replace('Z', '+00:00')) if course_data.get('end_at') else None,
                'is_public': course_data.get('is_public', False),
                'syllabus_body': course_data.get('syllabus_body', ''),
                'workflow_state': course_data.get('workflow_state', 'unpublished'),
                'time_zone': course_data.get('time_zone'),
                'uuid': course_data.get('uuid')
            }
        )
        return course

    @sync_to_async
    def _save_enrollment(self, enrollment_data: Dict, course: CanvasCourse) -> CanvasEnrollment:
        """Save enrollment data to the database (sync function)"""
        user_data = enrollment_data.get('user', {})

        enrollment, created = CanvasEnrollment.objects.update_or_create(
            canvas_id=enrollment_data['id'],
            course=course,
            defaults={
                'user_id': enrollment_data['user_id'],
                'user_name': user_data.get('name', 'Unknown User'),
                'sortable_name': user_data.get('sortable_name'),
                'short_name': user_data.get('short_name'),
                'email': user_data.get('email'),
                'role': enrollment_data.get('role', 'StudentEnrollment'),
                'enrollment_state': enrollment_data.get('enrollment_state', 'active'),
                'last_activity_at': datetime.fromisoformat(enrollment_data['last_activity_at'].replace('Z', '+00:00')) if enrollment_data.get('last_activity_at') else None,
                'grades': enrollment_data.get('grades', {})
            }
        )
        return enrollment

    @sync_to_async
    def _save_assignment(self, assignment_data: Dict, course: CanvasCourse) -> CanvasAssignment:
        """Save assignment data to the database (sync function)"""
        assignment, created = CanvasAssignment.objects.update_or_create(
            canvas_id=assignment_data['id'],
            course=course,
            defaults={
                'name': assignment_data['name'],
                'description': assignment_data.get('description', ''),
                'points_possible': assignment_data.get('points_possible', 0.0),
                'due_at': datetime.fromisoformat(assignment_data['due_at'].replace('Z', '+00:00')) if assignment_data.get('due_at') else None,
                'unlock_at': datetime.fromisoformat(assignment_data['unlock_at'].replace('Z', '+00:00')) if assignment_data.get('unlock_at') else None,
                'lock_at': datetime.fromisoformat(assignment_data['lock_at'].replace('Z', '+00:00')) if assignment_data.get('lock_at') else None,
                'position': assignment_data.get('position', 0),
                'grading_type': assignment_data.get('grading_type', 'points'),
                'published': assignment_data.get('published', False),
                'submission_types': assignment_data.get('submission_types', []),
                'has_submitted_submissions': assignment_data.get('has_submitted_submissions', False),
                'muted': assignment_data.get('muted', False),
                'html_url': assignment_data.get('html_url', ''),
                'has_overrides': assignment_data.get('has_overrides', False),
                'needs_grading_count': assignment_data.get('needs_grading_count', 0),
                'is_quiz_assignment': assignment_data.get('is_quiz_assignment', False)
            }
        )

        # If the assignment has a rubric, save it
        if 'rubric' in assignment_data and assignment_data['rubric'] and 'rubric_settings' in assignment_data:
            rubric_settings = assignment_data['rubric_settings']
            rubric, _ = CanvasRubric.objects.update_or_create(
                canvas_id=str(rubric_settings['id']),
                defaults={
                    'title': rubric_settings.get('title', 'Untitled Rubric'),
                    'points_possible': rubric_settings.get('points_possible', 0.0)
                }
            )

            # Save criteria and ratings
            for criterion_data in assignment_data['rubric']:
                criterion, _ = CanvasRubricCriterion.objects.update_or_create(
                    rubric=rubric,
                    canvas_id=criterion_data['id'],
                    defaults={
                        'description': criterion_data.get('description', ''),
                        'long_description': criterion_data.get('long_description', ''),
                        'points': criterion_data.get('points', 0.0),
                        'criterion_use_range': criterion_data.get('criterion_use_range', False)
                    }
                )

                # Save ratings for this criterion
                for rating_data in criterion_data.get('ratings', []):
                    CanvasRubricRating.objects.update_or_create(
                        criterion=criterion,
                        canvas_id=rating_data['id'],
                        defaults={
                            'description': rating_data.get('description', ''),
                            'long_description': rating_data.get('long_description', ''),
                            'points': rating_data.get('points', 0.0)
                        }
                    )

        return assignment

    @sync_to_async
    def _save_submission(self, submission_data: Dict, assignment: CanvasAssignment) -> Optional[CanvasSubmission]:
        """Save submission data to the database (sync function)"""
        # Find the enrollment
        try:
            enrollment = CanvasEnrollment.objects.get(
                course=assignment.course,
                user_id=submission_data['user_id']
            )
        except CanvasEnrollment.DoesNotExist:
            logger.warning(
                f"Enrollment not found for user {submission_data['user_id']} in course {assignment.course.canvas_id}")
            return None

        submission, created = CanvasSubmission.objects.update_or_create(
            canvas_id=submission_data['id'],
            assignment=assignment,
            enrollment=enrollment,
            defaults={
                'submitted_at': datetime.fromisoformat(submission_data['submitted_at'].replace('Z', '+00:00')) if submission_data.get('submitted_at') else None,
                'grade': submission_data.get('grade'),
                'score': submission_data.get('score'),
                'workflow_state': submission_data.get('workflow_state', 'unsubmitted'),
                'late': submission_data.get('late', False),
                'excused': submission_data.get('excused', False),
                'missing': submission_data.get('missing', False),
                'submission_type': submission_data.get('submission_type'),
                'url': submission_data.get('url'),
                'body': submission_data.get('body')
            }
        )
        return submission

    async def sync_course(self, course_id: int) -> CanvasCourse:
        """Sync a course and its enrollments, assignments, and submissions"""
        # Get course data
        course_data = await self.get_course(course_id)
        course = await self._save_course(course_data)

        # Get and sync enrollments
        enrollments_data = await self.get_enrollments(course_id)
        for enrollment_data in enrollments_data:
            await self._save_enrollment(enrollment_data, course)

        # Get and sync assignments
        assignments_data = await self.get_assignments(course_id)
        for assignment_data in assignments_data:
            assignment = await self._save_assignment(assignment_data, course)

            # Get and sync submissions for this assignment
            submissions_data = await self.get_submissions(course_id, assignment_data['id'])
            for submission_data in submissions_data:
                await self._save_submission(submission_data, assignment)

        # Update last sync timestamp
        self.integration.last_sync = datetime.now()
        await sync_to_async(self.integration.save)()

        return course

    async def sync_all_courses(self) -> List[CanvasCourse]:
        """Sync all available courses"""
        courses_data = await self.get_courses()
        synced_courses = []

        for course_data in courses_data:
            try:
                course = await self.sync_course(course_data['id'])
                synced_courses.append(course)
            except Exception as e:
                logger.error(f"Error syncing course {course_data['id']}: {e}")

        return synced_courses
