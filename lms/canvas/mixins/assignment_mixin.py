# File: lms/canvas/mixins/assignment_mixin.py
"""
Mixin providing assignment and submission related methods for Canvas API client.
"""
from datetime import datetime
from typing import Dict, List, Optional

from lms.utils import logger


class AssignmentMixin:
    """Provides assignment and submission related API methods"""

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

    async def _save_assignment(
            self, assignment_data: Dict, course: 'CanvasCourse'
    ) -> 'CanvasAssignment':
        """Save assignment data to the database using native async ORM"""
        assignment, created = await self.models.CanvasAssignment.objects.aupdate_or_create(
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
            rubric, _ = await self.models.CanvasRubric.objects.aupdate_or_create(
                canvas_id=str(rubric_settings["id"]),
                defaults={
                    "title": rubric_settings.get("title", "Untitled Rubric"),
                    "points_possible": rubric_settings.get("points_possible", 0.0),
                },
            )

            # Save criteria and ratings
            for criterion_data in assignment_data["rubric"]:
                criterion, _ = await self.models.CanvasRubricCriterion.objects.aupdate_or_create(
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
                    await self.models.CanvasRubricRating.objects.aupdate_or_create(
                        criterion=criterion,
                        canvas_id=rating_data["id"],
                        defaults={
                            "description": rating_data.get("description", ""),
                            "long_description": rating_data.get("long_description", ""),
                            "points": rating_data.get("points", 0.0),
                        },
                    )

        return assignment

    async def _save_submission(
            self, submission_data: Dict, assignment: 'CanvasAssignment'
    ) -> Optional['CanvasSubmission']:
        """Save submission data to the database using native async ORM"""
        # Find the enrollment
        try:
            enrollment = await self.models.CanvasEnrollment.objects.aget(
                course=assignment.course, user_id=submission_data["user_id"]
            )
        except self.models.CanvasEnrollment.DoesNotExist:
            logger.warning(
                f"Enrollment not found for user {submission_data['user_id']} in course {assignment.course.canvas_id}"
            )
            return None

        # Ensure excused field is always defined with a default value if not in submission_data
        excused = submission_data.get("excused")
        if excused is None:
            excused = False

        submission, created = await self.models.CanvasSubmission.objects.aupdate_or_create(
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