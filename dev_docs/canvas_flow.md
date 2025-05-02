# Canvas Data Import Flow

## Dependencies Overview

### Courses
- **Method**: `get_courses()`
- **Model**: `CanvasCourse`
- **Dependency**: None (entry point)

### Enrollments
- **Method**: `get_enrollments(course_id)`
- **Model**: `CanvasEnrollment`
- **Dependency**: 
  - `CanvasCourse` must exist first
  - Needs Student upsert

### Students
- Although not a Canvas API resource, during enrollment import upsert Student records based on enrollment data before creating `CanvasEnrollment`.

### Assignments
- **Method**: `get_assignments(course_id)`
- **Model**: `CanvasAssignment`
- **Dependency**: `CanvasCourse`

### Rubrics
- **Course-level rubrics**: 
  - `get_rubrics(course_id)` → `Rubric` + `RubricCriterion` + `RubricRating`
- **Assignment rubrics**: 
  - `get_assignment_rubrics(course_id, assignment_id)` → extend associations

### Rubric Associations
- Link Rubric to either `CanvasCourse` or `CanvasAssignment` → `RubricAssociation`

### Rubric Assessments
- **Method**: `get_rubric_assessments(course_id, rubric_id)`
- **Model**: `RubricAssessment`
- **Dependency**: `Rubric`, `RubricAssociation`, and `Student`

### Calendar Events
- **Method**: `get_calendar_events()`
- **Model**: `CalendarEvent`
- **Dependency**: `CanvasCourse`

### Submissions & Grades
- **Method**: `get_submissions(course_id, assignment_id)`
- **Model**: `Grade`
- **Dependency**: `CanvasAssignment` and `Student`

## Suggested Execution Order

1. Import Courses
2. Import Students & Enrollments
3. Import Assignments
4. *(Optional)* Import Rubrics & Criteria
5. Create Rubric Associations
6. *(Optional)* Import Rubric Assessments
7. *(Optional)* Import Calendar Events
8. Import Submissions → Grades

## Implementation Example

Each step can be its own asynchronous job, chained or kicked off in sequence:

```javascript
await import_courses(user)
await import_enrollments(user, course_id)
await import_assignments(user, course_id)
// …and so on…