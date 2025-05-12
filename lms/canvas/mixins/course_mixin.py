# File: lms/canvas/mixins/course_mixin.py
"""
Mixin providing course-related methods for Canvas API client.
"""
from datetime import datetime
from typing import Dict, List, Optional


class CourseMixin:
    """Provides course-related API methods"""

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

    async def get_course_users(self, course_id: int) -> List[Dict]:
        """Get all users (students, teachers, TAs, etc.) for a course with email information"""
        return await self.request(
            "GET",
            f"courses/{course_id}/users",
            params={"include[]": ["email", "enrollments"], "per_page": 100},
        )

    async def _save_course(self, course_data: Dict) -> 'CanvasCourse':
        """Save course data to the database using native async ORM"""
        defaults = {
            "name": course_data["name"],
            "course_code": course_data["course_code"],
            "start_at": (
                datetime.fromisoformat(course_data["start_at"].replace("Z", "+00:00"))
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
        }

        course, created = await self.models.CanvasCourse.objects.aupdate_or_create(
            canvas_id=course_data["id"],
            integration=self.integration,
            defaults=defaults
        )

        return course