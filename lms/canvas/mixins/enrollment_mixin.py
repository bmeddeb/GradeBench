# File: lms/canvas/mixins/enrollment_mixin.py
"""
Mixin providing enrollment-related methods for Canvas API client.
"""
from datetime import datetime
from typing import Dict, List, Optional


class EnrollmentMixin:
    """Provides enrollment-related API methods"""

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

    async def _save_enrollment(
            self, enrollment_data: Dict, course: 'CanvasCourse'
    ) -> 'CanvasEnrollment':
        """Save enrollment data to the database using native async ORM"""
        user_data = enrollment_data.get("user", {})

        enrollment, created = await self.models.CanvasEnrollment.objects.aupdate_or_create(
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
