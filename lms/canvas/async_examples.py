"""
Examples of using Canvas models with async queries.
"""
from lms.canvas.models import (
    CanvasCourse, CanvasAssignment, CanvasEnrollment, 
    CanvasSubmission, CanvasGroup, CanvasQuiz
)


async def get_active_courses():
    """Get all active courses with their enrollments using async queries."""
    courses = await CanvasCourse.objects.active().with_enrollments().aall()
    return courses


async def get_student_enrollments(course_id):
    """Get student enrollments for a course asynchronously."""
    enrollments = await (
        CanvasEnrollment.objects
        .for_course(course_id)
        .students_only()
        .active()
        .with_student_info()
        .aall()
    )
    return enrollments


async def get_assignment_with_submissions(assignment_id):
    """Get a specific assignment with all its submissions asynchronously."""
    try:
        assignment = await (
            CanvasAssignment.objects
            .with_submissions()
            .select_related('course')
            .aget(id=assignment_id)
        )
        return assignment
    except CanvasAssignment.DoesNotExist:
        return None


async def get_upcoming_assignments(course, days=7):
    """Get assignments due soon for a course asynchronously."""
    assignments = await (
        CanvasAssignment.objects
        .for_course(course)
        .due_soon(days=days)
        .published()
        .order_by('due_at')
        .aall()
    )
    return assignments


async def get_student_submissions(student_id):
    """Get all submissions for a student across all courses asynchronously."""
    submissions = await (
        CanvasSubmission.objects
        .for_student(student_id)
        .with_full_details()
        .select_related('assignment__course')
        .order_by('-submitted_at')
        .aall()
    )
    return submissions


async def get_course_groups(course_id):
    """Get all groups in a course with their members asynchronously."""
    groups = await (
        CanvasGroup.objects
        .for_course(course_id)
        .with_memberships()
        .with_core_team()
        .select_related('category')
        .aall()
    )
    return groups


async def check_submission_exists(assignment_id, enrollment_id):
    """Check if a submission exists for an assignment and enrollment asynchronously."""
    exists = await (
        CanvasSubmission.objects
        .filter(assignment_id=assignment_id, enrollment_id=enrollment_id)
        .aexists()
    )
    return exists


async def count_active_students(course_id):
    """Count active students in a course asynchronously."""
    count = await (
        CanvasEnrollment.objects
        .for_course(course_id)
        .students_only()
        .active()
        .acount()
    )
    return count


async def get_recent_quiz_scores(course_id, days=30):
    """Get recent quiz scores for a course asynchronously."""
    quizzes = await (
        CanvasQuiz.objects
        .for_course(course_id)
        .recent(days=days)
        .published()
        .with_assignment()
        .prefetch_related('assignment__submissions')
        .aall()
    )
    return quizzes


async def batch_update_submission_grades(submission_ids, grade):
    """Update multiple submission grades asynchronously."""
    updated_count = await (
        CanvasSubmission.objects
        .filter(id__in=submission_ids)
        .aupdate(grade=grade, workflow_state='graded')
    )
    return updated_count


# Example of using async context manager for transactions
from django.db import transaction

async def create_group_with_members(category_id, group_name, student_ids):
    """Create a new group and add members within a transaction."""
    async with transaction.atomic():
        # Create the group
        group = await CanvasGroup.objects.acreate(
            category_id=category_id,
            name=group_name,
            canvas_id=generate_canvas_id()  # You'd implement this
        )
        
        # Add members
        for student_id in student_ids:
            await CanvasGroupMembership.objects.acreate(
                group=group,
                student_id=student_id,
                user_id=get_canvas_user_id(student_id)  # You'd implement this
            )
        
        return group


# Example of combining async queries
async def get_course_analytics(course_id):
    """Get comprehensive analytics for a course using multiple async queries."""
    # Execute queries concurrently
    course, enrollments, assignments, submissions = await asyncio.gather(
        CanvasCourse.objects.select_related('integration').aget(id=course_id),
        CanvasEnrollment.objects.for_course(course_id).active().acount(),
        CanvasAssignment.objects.for_course(course_id).published().acount(),
        CanvasSubmission.objects.filter(
            assignment__course_id=course_id
        ).graded().acount()
    )
    
    return {
        'course': course,
        'active_enrollments': enrollments,
        'published_assignments': assignments,
        'graded_submissions': submissions
    }


# Example of async iterator
async def iterate_large_submission_set(assignment_id):
    """Iterate through a large set of submissions asynchronously."""
    async for submission in (
        CanvasSubmission.objects
        .for_assignment(assignment_id)
        .with_full_details()
        .order_by('submitted_at')
        .aiterator()
    ):
        # Process each submission
        yield await process_submission(submission)


async def process_submission(submission):
    """Process a single submission (placeholder for actual logic)."""
    # Your processing logic here
    return submission