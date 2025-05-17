# Canvas Models - Async Usage Guide

This guide demonstrates how to use Canvas models with Django's async ORM capabilities.

## Prerequisites

All Canvas models now inherit from `AsyncModelMixin`, which provides native async query support:
- `CanvasCourse`
- `CanvasEnrollment`
- `CanvasAssignment`
- `CanvasSubmission`
- `CanvasGroup`
- `CanvasGroupCategory`
- `CanvasGroupMembership`
- `CanvasQuiz`
- `CanvasRubric`
- `CanvasRubricCriterion`
- `CanvasRubricRating`

## Basic Async Queries

### Getting a single object
```python
# Sync version
course = CanvasCourse.objects.get(id=course_id)

# Async version
course = await CanvasCourse.objects.aget(id=course_id)
```

### Getting multiple objects
```python
# Sync version
enrollments = CanvasEnrollment.objects.filter(course=course).all()

# Async version
enrollments = await CanvasEnrollment.objects.filter(course=course).aall()
```

### Counting objects
```python
# Sync version
count = CanvasSubmission.objects.filter(assignment=assignment).count()

# Async version
count = await CanvasSubmission.objects.filter(assignment=assignment).acount()
```

### Checking existence
```python
# Sync version
exists = CanvasGroup.objects.filter(name="Team A").exists()

# Async version
exists = await CanvasGroup.objects.filter(name="Team A").aexists()
```

## Using Custom QuerySet Methods

All custom QuerySet methods work with async queries:

```python
# Get active courses with enrollments
courses = await CanvasCourse.objects.active().with_enrollments().aall()

# Get student enrollments for a course
enrollments = await (
    CanvasEnrollment.objects
    .for_course(course_id)
    .students_only()
    .active()
    .with_student_info()
    .aall()
)

# Get assignments due soon
assignments = await (
    CanvasAssignment.objects
    .due_soon(days=7)
    .published()
    .with_submissions()
    .aall()
)
```

## Async Aggregations

```python
# Get submission statistics
stats = await CanvasSubmission.objects.for_assignment(assignment).aaggregate(
    total=models.Count('id'),
    graded=models.Count('id', filter=models.Q(workflow_state='graded')),
    average_score=models.Avg('score')
)

# Count by enrollment type
enrollment_counts = await CanvasEnrollment.objects.for_course(course).aaggregate(
    students=models.Count('id', filter=models.Q(role='StudentEnrollment')),
    teachers=models.Count('id', filter=models.Q(role='TeacherEnrollment'))
)
```

## Async Updates

```python
# Update a single object
submission = await CanvasSubmission.objects.aget(id=submission_id)
submission.grade = 'A'
submission.workflow_state = 'graded'
await submission.asave()

# Bulk update
updated = await (
    CanvasSubmission.objects
    .filter(assignment_id=assignment_id, late=True)
    .aupdate(grade='F')
)
```

## Async Creates and Deletes

```python
# Create a new enrollment
enrollment = await CanvasEnrollment.objects.acreate(
    course=course,
    user_id=user_id,
    role='StudentEnrollment',
    enrollment_state='active'
)

# Delete objects
deleted_count = await (
    CanvasGroupMembership.objects
    .filter(group_id=group_id, student_id=student_id)
    .adelete()
)
```

## Async Transactions

```python
from django.db import transaction

async def create_assignment_with_rubric(course_id, assignment_data, rubric_data):
    async with transaction.atomic():
        # Create assignment
        assignment = await CanvasAssignment.objects.acreate(
            course_id=course_id,
            **assignment_data
        )
        
        # Create rubric
        rubric = await CanvasRubric.objects.acreate(
            title=rubric_data['title'],
            points_possible=rubric_data['points']
        )
        
        # Link them
        assignment.rubric = rubric
        await assignment.asave()
        
        return assignment
```

## Async Iteration

```python
# Iterate through large result sets
async for enrollment in CanvasEnrollment.objects.for_course(course).aiterator():
    # Process each enrollment
    await process_enrollment(enrollment)

# With chunking
async for chunk in CanvasSubmission.objects.for_assignment(assignment).aiterator(chunk_size=100):
    # Process chunk of submissions
    await process_submission_chunk(chunk)
```

## Concurrent Queries

```python
import asyncio

async def get_course_overview(course_id):
    # Execute multiple queries concurrently
    course, enrollments, assignments, submissions = await asyncio.gather(
        CanvasCourse.objects.aget(id=course_id),
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
```

## Async Views Example

```python
from django.views import View
from django.http import JsonResponse

class AsyncCourseView(View):
    async def get(self, request, course_id):
        try:
            # Get course with related data
            course = await (
                CanvasCourse.objects
                .select_related('integration')
                .prefetch_related('enrollments__student')
                .aget(id=course_id)
            )
            
            # Get course statistics
            stats = await self.get_course_stats(course_id)
            
            return JsonResponse({
                'course': {
                    'id': course.id,
                    'name': course.name,
                    'code': course.course_code
                },
                'statistics': stats
            })
            
        except CanvasCourse.DoesNotExist:
            return JsonResponse({'error': 'Course not found'}, status=404)
    
    async def get_course_stats(self, course_id):
        """Get course statistics using concurrent queries."""
        enrollment_stats, assignment_stats = await asyncio.gather(
            CanvasEnrollment.objects.for_course(course_id).aaggregate(
                total=models.Count('id'),
                active=models.Count('id', filter=models.Q(enrollment_state='active'))
            ),
            CanvasAssignment.objects.for_course(course_id).aaggregate(
                total=models.Count('id'),
                published=models.Count('id', filter=models.Q(published=True)),
                needs_grading=models.Count('id', filter=models.Q(needs_grading_count__gt=0))
            )
        )
        
        return {
            'enrollments': enrollment_stats,
            'assignments': assignment_stats
        }
```

## Best Practices

1. **Use `select_related` and `prefetch_related`** to avoid N+1 queries in async code:
   ```python
   enrollments = await (
       CanvasEnrollment.objects
       .select_related('student', 'course')
       .filter(course_id=course_id)
       .aall()
   )
   ```

2. **Batch operations** when possible:
   ```python
   # Instead of multiple individual queries
   for submission_id in submission_ids:
       submission = await CanvasSubmission.objects.aget(id=submission_id)
       submission.grade = 'A'
       await submission.asave()
   
   # Use bulk update
   await CanvasSubmission.objects.filter(id__in=submission_ids).aupdate(grade='A')
   ```

3. **Use concurrent queries** for independent operations:
   ```python
   # Execute independent queries concurrently
   results = await asyncio.gather(
       get_student_enrollments(student_id),
       get_student_submissions(student_id),
       get_student_groups(student_id)
   )
   ```

4. **Handle exceptions** properly in async code:
   ```python
   try:
       course = await CanvasCourse.objects.aget(id=course_id)
   except CanvasCourse.DoesNotExist:
       # Handle not found
       pass
   except Exception as e:
       # Handle other exceptions
       logger.error(f"Error fetching course: {e}")
   ```

5. **Use async context managers** for transactions:
   ```python
   async with transaction.atomic():
       # All database operations here are atomic
       await create_objects()
       await update_objects()
   ```