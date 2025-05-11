# Canvas LMS REST API – Guide to Push Operations (Create/Update Only)

This guide covers Canvas LMS REST API endpoints (for an Instructure-hosted Canvas instance) that are used exclusively for creating or updating data – i.e. “push” operations. Each section is organized by resource (Courses, Assignments, Groups, etc.), and for each endpoint we list the HTTP method, path, and a description of its function. Required parameters are noted, and key optional parameters are mentioned.

**Note:** All endpoints are under the base URL `https://<canvas-domain>/api/v1/`. We do not include any GET (read/list) or DELETE operations, only POST/PUT that create or modify resources.

## Courses

- **Create a Course** (`POST /api/v1/accounts/:account_id/courses`): Creates a new course under the specified account.  
  - **Required Path Params:** `account_id`  
  - **Optional Body Params:** `course[name]` (defaults to “Unnamed Course”), `course[course_code]`, `start_at`, `end_at`, `restrict_enrollments_to_course_dates`, `license`, `is_public`, `open_enrollment`, etc.

- **Update a Course** (`PUT /api/v1/courses/:id`): Updates an existing course’s settings.  
  - **Required Path Params:** `id` (course ID)  
  - **Body Params:** Fields from course creation to modify (e.g., `name`, `course_code`, dates, visibility settings, `syllabus_body`).

## Assignment Groups (Categories)

- **Create an Assignment Group** (`POST /api/v1/courses/:course_id/assignment_groups`):  
  - **Required Path Params:** `course_id`  
  - **Required Body Params:** `name`  
  - **Optional Body Params:** `position`, `group_weight`, `sis_source_id`, `rules`

- **Update an Assignment Group** (`PUT /api/v1/courses/:course_id/assignment_groups/:assignment_group_id`):  
  - **Required Path Params:** `course_id`, `assignment_group_id`  
  - **Body Params:** Fields from creation to update (e.g., `name`, `position`, `group_weight`).

## Assignments

- **Create an Assignment** (`POST /api/v1/courses/:course_id/assignments`):  
  - **Required Path Params:** `course_id`  
  - **Required Body Params:** `assignment[name]`  
  - **Optional Body Params:** `submission_types`, `allowed_extensions`, `points_possible`, `due_at`, `unlock_at`, `lock_at`, `group_category_id`, peer review settings, etc.

- **Update an Assignment** (`PUT /api/v1/courses/:course_id/assignments/:id`):  
  - **Required Path Params:** `course_id`, `id`  
  - **Body Params:** Fields from creation to update (e.g., title, description, points, dates, submission settings).

## Group Categories (Group Sets)

- **Create a Group Category** (`POST /api/v1/courses/:course_id/group_categories`):  
  - **Required Path Params:** `course_id`  
  - **Required Body Params:** `name`  
  - **Optional Body Params:** `self_signup`, `auto_leader`, `group_limit`, `create_group_count`

- **Update a Group Category** (`PUT /api/v1/group_categories/:group_category_id`):  
  - **Required Path Params:** `group_category_id`  
  - **Body Params:** `name`, `self_signup`, `group_limit`, etc.

## Groups

- **Create a Group** (`POST /api/v1/group_categories/:group_category_id/groups`):  
  - **Required Path Params:** `group_category_id`  
  - **Optional Body Params:** `name`, `description`, (for community groups) `is_public`, `join_level`

- **Update a Group** (`PUT /api/v1/groups/:group_id`):  
  - **Required Path Params:** `group_id`  
  - **Body Params:** `name`, `description`, `is_public` (community groups), `join_level`, `avatar_id`, `members[]`

## Students (Enrollments & Group Memberships)

- **Enroll a User in a Course** (`POST /api/v1/courses/:course_id/enrollments`):  
  - **Required Path Params:** `course_id`  
  - **Required Body Params:** `enrollment[user_id]`, `enrollment[type]`  
  - **Optional Body Params:** `enrollment[course_section_id]`, `enrollment[enrollment_state]`, `enrollment[notify]`

- **Add User to a Group** (`PUT /api/v1/groups/:group_id/users/:user_id`):  
  - **Required Path Params:** `group_id`, `user_id`  
  - **Optional Body Params:** `moderator=true`

## Rubrics

- **Create a Rubric** (`POST /api/v1/courses/:course_id/rubrics`):  
  - **Required Path Params:** `course_id`  
  - **Required Body Params:** `rubric[title]`, `rubric[criteria]`  
  - **Optional Body Params:** `rubric_association[association_id]`, `rubric_association[association_type]`, `rubric_association[use_for_grading]`, `rubric_association[hide_score_total]`, `purpose`

- **Update a Rubric** (`PUT /api/v1/courses/:course_id/rubrics/:id`):  
  - **Required Path Params:** `course_id`, `id`  
  - **Body Params:** Fields from creation to update criteria, title, association settings

- **Attach Rubric to Assignment** (`POST /api/v1/courses/:course_id/rubric_associations`):  
  - **Required Path Params:** `course_id`  
  - **Required Body Params:** `rubric_association[rubric_id]`, `association_id`, `association_type`  
  - **Optional Body Params:** `use_for_grading`, `hide_score_total`, `purpose`

- **Update Rubric Association** (`PUT /api/v1/courses/:course_id/rubric_associations/:id`):  
  - **Required Path Params:** `course_id`, `id`  
  - **Body Params:** Same as creation

## Pages

- **Create a Page** (`POST /api/v1/courses/:course_id/pages`):  
  - **Required Path Params:** `course_id`  
  - **Required Body Params:** `wiki_page[title]`  
  - **Optional Body Params:** `wiki_page[body]`, `wiki_page[published]`, `wiki_page[editing_roles]`, `wiki_page[notify_of_update]`

- **Update a Page** (`PUT /api/v1/courses/:course_id/pages/:url`):  
  - **Required Path Params:** `course_id`, `url` (or `page_id:<id>`)  
  - **Body Params:** Same as creation

- **Update Front Page** (`PUT /api/v1/courses/:course_id/front_page`):  
  - **Required Path Params:** `course_id`  
  - **Body Params:** Same as page update

## Discussion Topics

- **Create a Discussion** (`POST /api/v1/courses/:course_id/discussion_topics`):  
  - **Required Path Params:** `course_id`  
  - **Required Body Params:** `title`  
  - **Optional Body Params:** `message`, `discussion_type`, `published`, `delayed_post_at`, `lock_at`, `podcast_enabled`, `require_initial_post`, graded discussion `assignment[...]`, `is_announcement`

- **Update a Discussion** (`PUT /api/v1/courses/:course_id/discussion_topics/:topic_id`):  
  - **Required Path Params:** `course_id`, `topic_id`  
  - **Body Params:** Same as creation

## Quizzes (Classic)

- **Create a Quiz** (`POST /api/v1/courses/:course_id/quizzes`):  
  - **Required Path Params:** `course_id`  
  - **Required Body Params:** `quiz[title]`  
  - **Optional Body Params:** `quiz[description]`, `quiz[quiz_type]`, `quiz[assignment_group_id]`, `quiz[time_limit]`, `quiz[shuffle_answers]`, `quiz[allowed_attempts]`, `quiz[scoring_policy]`, `quiz[hide_results]`, `quiz[show_correct_answers]`, `quiz[due_at]`, `quiz[unlock_at]`, `quiz[lock_at]`, `quiz[published]`

- **Update a Quiz** (`PUT /api/v1/courses/:course_id/quizzes/:id`):  
  - **Required Path Params:** `course_id`, `id`  
  - **Body Params:** Same as creation

## Modules

- **Create a Module** (`POST /api/v1/courses/:course_id/modules`):  
  - **Required Path Params:** `course_id`  
  - **Required Body Params:** `module[name]`  
  - **Optional Body Params:** `module[position]`, `module[unlock_at]`, `module[require_sequential_progress]`, `module[prerequisite_module_ids]`, `module[published]`

- **Update a Module** (`PUT /api/v1/courses/:course_id/modules/:id`):  
  - **Required Path Params:** `course_id`, `id`  
  - **Body Params:** Same as creation

- **Add a Module Item** (`POST /api/v1/courses/:course_id/modules/:module_id/items`):  
  - **Required Path Params:** `course_id`, `module_id`  
  - **Required Body Params:** `module_item[type]`, `module_item[content_id]` or `module_item[page_url]`  
  - **Optional Body Params:** `module_item[title]`, `module_item[position]`, `module_item[indent]`, `module_item[completion_requirement]`

### Update a Module Item

**Endpoint:**  
```http
PUT /api/v1/courses/:course_id/modules/:module_id/items/:id
```

**Description:**  
Updates an existing module item’s attributes. Any provided fields will overwrite the current values.

**Path Parameters:**
- `:course_id` — ID of the course  
- `:module_id` — ID of the module  
- `:id` — ID of the module item  

**Body Parameters (all optional):**
- `module_item[title]` *(string)* — Custom label for the module item  
- `module_item[position]` *(integer)* — Order of the item within the module  
- `module_item[indent]` *(integer)* — Indentation level for display  
- `module_item[completion_requirement]` *(hash)* — Completion rules (e.g. `{ "type": "min_score", "min_score": 10 }`; omit or clear to remove requirements)  

> **Note:**  
> - Uses the same fields as the **Create Module Item** endpoint.  
> - To mark an item complete for a student, use the separate “Mark as Complete” endpoint—this PUT is only for reordering, relabeling, and changing requirements.  
```
