"""
Async views for Canvas models demonstrating async ORM usage.
"""
from django.views.generic import View
from django.http import JsonResponse
from asgiref.sync import sync_to_async
import json

from lms.canvas.models import (
    CanvasCourse, CanvasEnrollment, CanvasAssignment,
    CanvasSubmission, CanvasGroup
)


class AsyncCanvasView(View):
    """Base async view for Canvas operations."""
    
    async def dispatch(self, request, *args, **kwargs):
        """Override dispatch to handle async methods."""
        method = request.method.lower()
        handler = getattr(self, method, self.http_method_not_allowed)
        return await handler(request, *args, **kwargs)


class CourseEnrollmentsView(AsyncCanvasView):
    """Async view to get course enrollments."""
    
    async def get(self, request, course_id):
        try:
            # Get course with integration details
            course = await CanvasCourse.objects.select_related('integration').aget(id=course_id)
            
            # Get active student enrollments
            enrollments = await (
                CanvasEnrollment.objects
                .for_course(course)
                .students_only()
                .active()
                .with_student_info()
                .values(
                    'id', 'user_name', 'email',
                    'student__first_name', 'student__last_name',
                    'last_activity_at'
                )
                .aall()
            )
            
            return JsonResponse({
                'course': {
                    'id': course.id,
                    'name': course.name,
                    'code': course.course_code
                },
                'enrollments': list(enrollments),
                'count': len(enrollments)
            })
            
        except CanvasCourse.DoesNotExist:
            return JsonResponse({'error': 'Course not found'}, status=404)


class AssignmentSubmissionsView(AsyncCanvasView):
    """Async view to get assignment submissions."""
    
    async def get(self, request, assignment_id):
        try:
            # Get assignment with course details
            assignment = await (
                CanvasAssignment.objects
                .select_related('course')
                .aget(id=assignment_id)
            )
            
            # Get all submissions for the assignment
            submissions = await (
                CanvasSubmission.objects
                .for_assignment(assignment)
                .with_full_details()
                .values(
                    'id', 'submitted_at', 'grade', 'score', 'late',
                    'enrollment__user_name', 'enrollment__student__email'
                )
                .aall()
            )
            
            # Get submission statistics
            stats = await CanvasSubmission.objects.for_assignment(assignment).aaggregate(
                total=models.Count('id'),
                graded=models.Count('id', filter=models.Q(workflow_state='graded')),
                late=models.Count('id', filter=models.Q(late=True)),
                average_score=models.Avg('score', filter=models.Q(score__isnull=False))
            )
            
            return JsonResponse({
                'assignment': {
                    'id': assignment.id,
                    'name': assignment.name,
                    'points_possible': assignment.points_possible,
                    'due_at': assignment.due_at.isoformat() if assignment.due_at else None
                },
                'submissions': list(submissions),
                'statistics': stats
            })
            
        except CanvasAssignment.DoesNotExist:
            return JsonResponse({'error': 'Assignment not found'}, status=404)


class StudentDashboardView(AsyncCanvasView):
    """Async view to get student dashboard data."""
    
    async def get(self, request, student_id):
        # Execute multiple queries concurrently
        enrollments, submissions, groups = await asyncio.gather(
            self._get_student_enrollments(student_id),
            self._get_recent_submissions(student_id),
            self._get_student_groups(student_id)
        )
        
        return JsonResponse({
            'student_id': student_id,
            'enrollments': enrollments,
            'recent_submissions': submissions,
            'groups': groups
        })
    
    async def _get_student_enrollments(self, student_id):
        """Get all active enrollments for a student."""
        enrollments = await (
            CanvasEnrollment.objects
            .for_student(student_id)
            .active()
            .with_course()
            .values('id', 'course__name', 'course__course_code', 'role')
            .aall()
        )
        return list(enrollments)
    
    async def _get_recent_submissions(self, student_id, limit=10):
        """Get recent submissions for a student."""
        submissions = await (
            CanvasSubmission.objects
            .for_student(student_id)
            .select_related('assignment__course')
            .order_by('-submitted_at')
            .values(
                'id', 'submitted_at', 'grade', 
                'assignment__name', 'assignment__course__name'
            )[:limit]
            .aall()
        )
        return list(submissions)
    
    async def _get_student_groups(self, student_id):
        """Get all groups a student belongs to."""
        groups = await (
            CanvasGroup.objects
            .filter(memberships__student_id=student_id)
            .with_category()
            .values('id', 'name', 'category__name', 'category__course__name')
            .aall()
        )
        return list(groups)


class BulkGradeUpdateView(AsyncCanvasView):
    """Async view to update grades in bulk."""
    
    async def post(self, request):
        try:
            data = json.loads(request.body)
            submission_updates = data.get('submissions', [])
            
            # Update grades concurrently
            update_tasks = [
                self._update_submission_grade(
                    sub['id'], 
                    sub['grade'], 
                    sub.get('comment')
                )
                for sub in submission_updates
            ]
            
            results = await asyncio.gather(*update_tasks, return_exceptions=True)
            
            # Count successes and failures
            successes = sum(1 for r in results if not isinstance(r, Exception))
            failures = sum(1 for r in results if isinstance(r, Exception))
            
            return JsonResponse({
                'total': len(submission_updates),
                'successes': successes,
                'failures': failures,
                'results': [
                    {'id': sub['id'], 'status': 'success' if not isinstance(results[i], Exception) else 'failed'}
                    for i, sub in enumerate(submission_updates)
                ]
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON'}, status=400)
    
    async def _update_submission_grade(self, submission_id, grade, comment=None):
        """Update a single submission grade."""
        try:
            submission = await CanvasSubmission.objects.aget(id=submission_id)
            submission.grade = grade
            submission.workflow_state = 'graded'
            if comment:
                submission.grader_comment = comment
            await submission.asave(update_fields=['grade', 'workflow_state', 'grader_comment'])
            return submission
        except CanvasSubmission.DoesNotExist:
            raise ValueError(f"Submission {submission_id} not found")


# Example async API endpoint
async def course_analytics_api(request, course_id):
    """API endpoint to get course analytics asynchronously."""
    try:
        # Execute multiple aggregations concurrently
        course, stats = await asyncio.gather(
            CanvasCourse.objects.aget(id=course_id),
            CanvasEnrollment.objects.for_course(course_id).aaggregate(
                total_students=models.Count('id', filter=models.Q(role='StudentEnrollment')),
                active_students=models.Count(
                    'id', 
                    filter=models.Q(role='StudentEnrollment', enrollment_state='active')
                ),
                total_teachers=models.Count('id', filter=models.Q(role='TeacherEnrollment'))
            )
        )
        
        # Get assignment statistics
        assignment_stats = await CanvasAssignment.objects.for_course(course_id).aaggregate(
            total_assignments=models.Count('id'),
            published_assignments=models.Count('id', filter=models.Q(published=True)),
            assignments_needing_grading=models.Count('id', filter=models.Q(needs_grading_count__gt=0))
        )
        
        return JsonResponse({
            'course': {
                'id': course.id,
                'name': course.name,
                'code': course.course_code,
                'state': course.workflow_state
            },
            'enrollment_stats': stats,
            'assignment_stats': assignment_stats
        })
        
    except CanvasCourse.DoesNotExist:
        return JsonResponse({'error': 'Course not found'}, status=404)