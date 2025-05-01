# lms/canvas/client.py
import httpx
from django.conf import settings
from typing import Any, Dict, List

class CanvasClient:
    """
    Async HTTP client for Canvas LMS API, using a personal access token.
    """
    def __init__(self, token: str, timeout: float = 10.0):
        self._base_url = settings.CANVAS_API_URL.rstrip('/')
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=timeout,
        )

    async def get_courses(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch the list of courses accessible to the user."""
        response = await self._client.get(
            "/api/v1/courses",
            params={"per_page": per_page},
        )
        response.raise_for_status()
        return response.json()

    async def get_enrollments(self, course_id: int, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch enrollments for a given course."""
        response = await self._client.get(
            f"/api/v1/courses/{course_id}/enrollments",
            params={"per_page": per_page},
        )
        response.raise_for_status()
        return response.json()

    async def get_assignments(self, course_id: int, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch assignments for a given course."""
        response = await self._client.get(
            f"/api/v1/courses/{course_id}/assignments",
            params={"per_page": per_page},
        )
        response.raise_for_status()
        return response.json()

    async def get_rubrics(self, course_id: int, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch rubrics at the course level."""
        response = await self._client.get(
            f"/api/v1/courses/{course_id}/rubrics",
            params={"per_page": per_page},
        )
        response.raise_for_status()
        return response.json()

    async def get_assignment_rubrics(self, course_id: int, assignment_id: int, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch rubrics attached to a specific assignment."""
        response = await self._client.get(
            f"/api/v1/courses/{course_id}/assignments/{assignment_id}/rubrics",
            params={"per_page": per_page},
        )
        response.raise_for_status()
        return response.json()

    async def get_rubric_assessments(self, course_id: int, rubric_id: int, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch rubric assessments for a given rubric."""
        response = await self._client.get(
            f"/api/v1/courses/{course_id}/rubrics/{rubric_id}/assessments",
            params={"per_page": per_page},
        )
        response.raise_for_status()
        return response.json()

    async def get_calendar_events(self, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch calendar events (optionally filter by context codes)."""
        response = await self._client.get(
            "/api/v1/calendar_events",
            params={"per_page": per_page},
        )
        response.raise_for_status()
        return response.json()

    async def get_submissions(self, course_id: int, assignment_id: int, per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch submissions for a given assignment."""
        response = await self._client.get(
            f"/api/v1/courses/{course_id}/assignments/{assignment_id}/submissions",
            params={"per_page": per_page},
        )
        response.raise_for_status()
        return response.json()

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()
