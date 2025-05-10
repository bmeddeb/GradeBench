#!/usr/bin/env python3
"""
Standalone script to inspect Canvas API JSON responses using an inline CanvasClient.

This does NOT depend on Django—just Python 3.8+ and httpx.

Usage:
  python dev_docs/examples/inspect_canvas_api_simple.py --token <CANVAS_PERSONAL_ACCESS_TOKEN> \
      --base-url https://canvas.instructure.com
"""
import asyncio
import argparse
import json
import httpx

class CanvasClient:
    """
    Async HTTP client for Canvas LMS API, using a personal access token.
    """
    def __init__(self, token: str, base_url: str, timeout: float = 10.0):
        self._base_url = base_url.rstrip('/')
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            headers=headers,
            timeout=timeout,
        )

    async def get_courses(self, per_page: int = 100):
        resp = await self._client.get(
            "/api/v1/courses",
            params={"per_page": per_page},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_enrollments(self, course_id: int, per_page: int = 100):
        resp = await self._client.get(
            f"/api/v1/courses/{course_id}/enrollments",
            params={"per_page": per_page},
        )
        resp.raise_for_status()
        return resp.json()

    async def get_assignments(self, course_id: int, per_page: int = 100):
        resp = await self._client.get(
            f"/api/v1/courses/{course_id}/assignments",
            params={"per_page": per_page},
        )
        resp.raise_for_status()
        return resp.json()

    async def close(self):
        await self._client.aclose()


def parse_args():
    p = argparse.ArgumentParser(description="Inspect Canvas API via httpx")
    p.add_argument("--token", "-t", required=True,
                   help="Canvas personal access token")
    p.add_argument("--base-url", "-u", required=True,
                   help="Canvas base URL, e.g. https://canvas.instructure.com")
    return p.parse_args()


async def main():
    args = parse_args()
    client = CanvasClient(args.token, args.base_url)

    print("\n=== Fetching Courses ===")
    courses = await client.get_courses()
    print(json.dumps(courses, indent=2))

    if not courses:
        print("No courses found; verify your token and base URL.")
        await client.close()
        return

    first = courses[0]
    course_id = first.get('id') or first.get('course_id')
    print(f"\n=== First Course ID: {course_id} ===")

    print("\n=== Fetching Enrollments ===")
    enrollments = await client.get_enrollments(course_id)
    print(json.dumps(enrollments, indent=2))

    print("\n=== Fetching Assignments ===")
    assignments = await client.get_assignments(course_id)
    print(json.dumps(assignments, indent=2))

    await client.close()

if __name__ == '__main__':
    asyncio.run(main())
