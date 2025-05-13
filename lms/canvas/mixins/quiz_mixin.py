# File: lms/canvas/mixins/quiz_mixin.py
"""
Mixin providing quiz-related methods for Canvas API client.
"""
from datetime import datetime
from typing import Dict, List, Optional

from lms.utils import logger


class QuizMixin:
    """Provides quiz-related API methods"""

    async def get_quizzes(self, course_id: int) -> List[Dict]:
        """Get all quizzes for a course"""
        return await self.request(
            "GET",
            f"courses/{course_id}/quizzes",
            params={"per_page": 100},
        )

    async def get_quiz(self, course_id: int, quiz_id: int) -> Dict:
        """Get a single quiz by ID"""
        return await self.request(
            "GET",
            f"courses/{course_id}/quizzes/{quiz_id}",
        )

    async def _save_quiz(
            self, quiz_data: Dict, course: 'CanvasCourse'
    ) -> 'CanvasQuiz':
        """Save quiz data to the database using native async ORM"""
        
        # First, check if there's an associated assignment
        assignment = None
        if quiz_data.get("assignment_id"):
            try:
                assignment = await self.models.CanvasAssignment.objects.aget(
                    canvas_id=quiz_data["assignment_id"],
                    course=course
                )
                # Update the is_quiz_assignment flag
                assignment.is_quiz_assignment = True
                await assignment.asave()
            except self.models.CanvasAssignment.DoesNotExist:
                logger.warning(
                    f"Assignment not found for quiz {quiz_data['id']} in course {course.id}"
                )
        
        quiz, created = await self.models.CanvasQuiz.objects.aupdate_or_create(
            canvas_id=quiz_data["id"],
            course=course,
            defaults={
                "title": quiz_data["title"],
                "description": quiz_data.get("description", ""),
                "quiz_type": quiz_data.get("quiz_type", "assignment"),
                "assignment": assignment,
                "time_limit": quiz_data.get("time_limit"),
                "shuffle_answers": quiz_data.get("shuffle_answers", False),
                "one_question_at_a_time": quiz_data.get("one_question_at_a_time", False),
                "show_correct_answers": quiz_data.get("show_correct_answers", True),
                "hide_results": quiz_data.get("hide_results"),
                "due_at": (
                    datetime.fromisoformat(
                        quiz_data["due_at"].replace("Z", "+00:00")
                    )
                    if quiz_data.get("due_at")
                    else None
                ),
                "unlock_at": (
                    datetime.fromisoformat(
                        quiz_data["unlock_at"].replace("Z", "+00:00")
                    )
                    if quiz_data.get("unlock_at")
                    else None
                ),
                "lock_at": (
                    datetime.fromisoformat(
                        quiz_data["lock_at"].replace("Z", "+00:00")
                    )
                    if quiz_data.get("lock_at")
                    else None
                ),
                "points_possible": quiz_data.get("points_possible", 0.0),
                "scoring_policy": quiz_data.get("scoring_policy"),
                "published": quiz_data.get("published", False),
            },
        )
        
        return quiz
        
    async def sync_course_quizzes(self, course_id: int) -> List['CanvasQuiz']:
        """Sync all quizzes for a course from Canvas API"""
        course = await self.models.CanvasCourse.objects.aget(canvas_id=course_id)
        quizzes_data = await self.get_quizzes(course_id)
        
        saved_quizzes = []
        for quiz_data in quizzes_data:
            quiz = await self._save_quiz(quiz_data, course)
            saved_quizzes.append(quiz)
            
        return saved_quizzes