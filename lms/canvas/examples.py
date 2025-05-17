"""
Examples of using Canvas model QuerySets and Managers to avoid N+1 queries.
"""
from lms.canvas.models import CanvasCourse, CanvasAssignment, CanvasEnrollment, CanvasSubmission, CanvasGroupCategory

# Example 1: Fetch active courses with their enrollments
active_courses = (
    CanvasCourse.objects
    .active()
    .with_enrollments()
    .select_related('integration')
)

# Example 2: Get all assignments due soon with their submissions
upcoming_assignments = (
    CanvasAssignment.objects
    .due_soon(days=7)
    .published()
    .with_submissions()
    .select_related('course')
)

# Example 3: Get student enrollments for a specific course
student_enrollments = (
    CanvasEnrollment.objects
    .for_course(course_id)
    .students_only()
    .active()
    .with_student_info()
)

# Example 4: Get all groups in a course with their members
course_groups = (
    CanvasGroup.objects
    .for_course(course_id)
    .with_memberships()
    .with_core_team()
    .select_related('category')
)

# Example 5: Complex query - published assignments with submissions needing grading
assignments_to_grade = (
    CanvasAssignment.objects
    .published()
    .needs_grading()
    .with_course()
    .prefetch_related(
        'submissions__enrollment__student'
    )
    .order_by('due_at')
)

# Example 6: Get recent quizzes with their associated assignments
recent_quizzes = (
    CanvasQuiz.objects
    .recent(days=30)
    .published()
    .graded_quizzes()
    .with_assignment()
    .select_related('course')
)

# Example 7: Chained filtering - active students in current courses
current_students = (
    CanvasEnrollment.objects
    .students_only()
    .active()
    .filter(course__in=CanvasCourse.objects.current())
    .with_student_info()
    .distinct()
)

# Example 8: Group categories with self-signup enabled
self_signup_groups = (
    CanvasGroupCategory.objects
    .self_signup_enabled()
    .with_groups()
    .with_memberships()
    .filter(course__workflow_state='available')
)

# Example 9: Late submissions for a specific assignment
late_submissions = (
    CanvasSubmission.objects
    .for_assignment(assignment_id)
    .late()
    .with_full_details()
    .order_by('submitted_at')
)

# Example 10: All submissions for a student across all courses
student_submissions = (
    CanvasSubmission.objects
    .for_student(student_id)
    .with_full_details()
    .select_related('assignment__course')
    .order_by('-submitted_at')
)