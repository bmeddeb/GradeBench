# Canvas LMS API: Assignments, Quizzes, and Rubrics (Hosted by Instructure Cloud)

## Overview

This report covers:
- All available **CRUD** operations (`Create`, `Read`, `Update`, `Delete`)
- **Data structures** (request/response fields, data types)
- **Relationships** between models (Assignments, Quizzes, Rubrics)
- **Authorization requirements**
- A **note** about **GraphQL** future support

---

## 1. Assignments

### Endpoints
- `GET /api/v1/courses/:course_id/assignments` — List all assignments
- `GET /api/v1/users/:user_id/courses/:course_id/assignments` — List assignments visible to a specific user
- `GET /api/v1/courses/:course_id/assignments/:id` — Get one assignment
- `POST /api/v1/courses/:course_id/assignments` — Create new assignment
- `PUT /api/v1/courses/:course_id/assignments/:id` — Update existing assignment
- `DELETE /api/v1/courses/:course_id/assignments/:id` — Delete assignment

### Data Structure
- **ID**: integer
- **Name**: string
- **Description**: HTML string
- **Dates**: `due_at`, `lock_at`, `unlock_at` (ISO datetime or null)
- **Course Link**: `course_id`
- **Assignment Group Link**: `assignment_group_id`
- **Submission Types**: array (e.g., `["online_upload"]`)
- **Grading Type**: string (e.g., `"points"`)
- **Other Fields**: `published` (boolean), `points_possible` (float), etc.

### Related Models
- Belongs to a Course (`course_id`)
- May belong to an Assignment Group (`assignment_group_id`)
- May be linked to a Quiz (`quiz_id`)
- Can have Rubric associations

### Authorization
- OAuth2 Bearer token
- Role: Instructor or Admin required for create/update/delete

### GraphQL Note
- Partial GraphQL support for Assignments via `assignmentsConnection`
- Quiz-related assignment fields available but **limited**

---

## 2. Quizzes

### Endpoints
- `GET /api/v1/courses/:course_id/quizzes` — List quizzes
- `GET /api/v1/courses/:course_id/quizzes/:id` — Get one quiz
- `POST /api/v1/courses/:course_id/quizzes` — Create new quiz
- `PUT /api/v1/courses/:course_id/quizzes/:id` — Update quiz
- `DELETE /api/v1/courses/:course_id/quizzes/:id` — Delete quiz
- (Extra: reorder questions, validate access codes)

### Data Structure
- **ID**: integer
- **Title**: string
- **Description**: HTML string
- **Quiz Type**: `"assignment"`, `"practice_quiz"`, etc.
- **Time Limit**: integer (minutes)
- **Settings**: `shuffle_answers`, `one_question_at_a_time`, etc.
- **Visibility Controls**: `show_correct_answers`, `hide_results`
- **Dates**: `due_at`, `lock_at`, `unlock_at`
- **Scoring**: `points_possible`, `scoring_policy`
- **Status**: `published` (boolean)

### Related Models
- Belongs to a Course
- Also appears as an Assignment (via `submission_types=["online_quiz"]`)
- Questions are separate under Quiz Questions API
- Submissions tracked separately

### Authorization
- OAuth2 Bearer token
- Role: Instructor or Admin for CRUD operations

### GraphQL Note
- **No direct GraphQL** support for quizzes currently

---

## 3. Rubrics

### Endpoints
- `GET /api/v1/courses/:course_id/rubrics` — List rubrics
- `GET /api/v1/courses/:course_id/rubrics/:id` — Get one rubric
- `POST /api/v1/courses/:course_id/rubrics` — Create rubric
- `PUT /api/v1/courses/:course_id/rubrics/:id` — Update rubric
- `DELETE /api/v1/courses/:course_id/rubrics/:id` — Delete rubric

(Also: `GET /rubrics/:id/used_locations` to find associated locations)

### Data Structure
- **ID**: integer
- **Title**: string
- **Context ID**: integer (Course or Account)
- **Points Possible**: float
- **Flags**: `reusable`, `read_only`, `free_form_criterion_comments`
- **Criteria**: Array of criterion objects (ratings, points, descriptions)

Rubric Criterion:
- **ID**: string
- **Points**: float
- **Ratings**: array (each rating has ID, points, description)

Rubric Association:
- **Association ID**: integer (Assignment/Course ID)
- **Association Type**: `"Assignment"` or `"Course"`
- **Use for Grading**: boolean

### Related Models
- Belongs to Course or Account
- Associated with Assignments (for grading) via RubricAssociation
- Grading records via RubricAssessment (separate)

### Authorization
- OAuth2 Bearer token
- Role: Instructor or Admin for CRUD

### GraphQL Note
- **No GraphQL** support for Rubrics at this time

---

## Notes

- All endpoints use Bearer tokens (`Authorization: Bearer <token>`)
- Data types mainly include: integer, string, array, float, boolean, and ISO datetime
- REST remains the primary interface
- GraphQL expansion is ongoing (partial for Assignments, none yet for Quizzes and Rubrics)

---

## References
- Canvas LMS API Docs (Assignments, Quizzes, Rubrics)
- Canvas Open API GitHub
