# Canvas LMS API Data Structures and Pydantic Models

This document covers **Students**, **Courses**, **Groups**, and **Group Sets (Categories)** for the Canvas LMS REST API. It includes field lists, data types, nullability, and Pydantic model examples.

---

## Students

### Fields
| Field            | Type            | Nullable? | Description |
|------------------|-----------------|-----------|-------------|
| `id`             | integer         | No        | Unique Canvas user ID |
| `name`           | string          | No        | Full name of the user |
| `sortable_name`  | string          | No        | Name formatted for sorting |
| `short_name`     | string          | No        | User’s short display name |
| `sis_user_id`    | string          | Yes       | SIS ID (optional) |
| `sis_import_id`  | integer          | Yes       | SIS import ID (optional) |
| `sis_login_id`   | string          | Yes       | Deprecated SIS login ID |
| `integration_id` | string          | Yes       | Integration ID |
| `login_id`       | string          | No        | Login ID (email or username) |
| `avatar_url`     | string          | Yes       | Avatar image URL |
| `enrollments`    | array or null   | Yes       | List of enrollments |
| `email`          | string          | Yes       | Primary email |
| `locale`         | string          | Yes       | User locale |
| `last_login`     | datetime string | Yes       | Last login timestamp |
| `time_zone`      | string          | Yes       | User’s timezone |
| `bio`            | string          | Yes       | User bio |

### Pydantic Model
```python
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

class Student(BaseModel):
    id: int
    name: str
    sortable_name: str
    short_name: str
    sis_user_id: Optional[str] = None
    sis_import_id: Optional[int] = None
    sis_login_id: Optional[str] = None
    integration_id: Optional[str] = None
    login_id: str
    avatar_url: Optional[str] = None
    enrollments: Optional[List[dict]] = None
    email: Optional[str] = None
    locale: Optional[str] = None
    last_login: Optional[datetime] = None
    time_zone: Optional[str] = None
    bio: Optional[str] = None
```

---

## Courses

### Fields
| Field | Type | Nullable? | Description |
|------|------|-----------|-------------|
| `id` | integer | No | Unique Canvas course ID |
| `sis_course_id` | string | Yes | SIS course ID |
| `uuid` | string | No | Course UUID |
| `integration_id` | string | Yes | Integration ID |
| `sis_import_id` | integer | Yes | SIS import ID |
| `name` | string | No | Course name |
| `course_code` | string | No | Short course code |
| `original_name` | string | Yes | Original name |
| `workflow_state` | string | No | Course status |
| `account_id` | integer | No | Account ID |
| `root_account_id` | integer | No | Root account ID |
| `enrollment_term_id` | integer | No | Enrollment term ID |
| `grading_periods` | array or null | Yes | Grading periods |
| `grading_standard_id` | integer | Yes | Grading standard ID |
| `grade_passback_setting` | string | No | Grade passback setting |
| `created_at` | datetime string | No | Course creation timestamp |
| `start_at` | datetime string | Yes | Course start time |
| `end_at` | datetime string | Yes | Course end time |
| `locale` | string | No | Course locale |
| `enrollments` | array or null | Yes | Enrollments list |
| `total_students` | integer | Yes | Total students count |
| `calendar` | object or null | Yes | Calendar link |
| `default_view` | string | No | Default page view |
| `syllabus_body` | string | Yes | Syllabus content |
| `needs_grading_count` | integer | Yes | Assignments needing grading |
| `term` | object or null | Yes | Term object |
| `course_progress` | object or null | Yes | Course progress |
| `apply_assignment_group_weights` | boolean | No | Assignment weighting flag |
| `permissions` | object | Yes | Permissions object |
| `is_public` | boolean | No | Public visibility |
| `is_public_to_auth_users` | boolean | No | Public to auth users |
| `public_syllabus` | boolean | No | Syllabus visibility |
| `public_syllabus_to_auth` | boolean | No | Syllabus auth visibility |
| `public_description` | string | Yes | Public course description |
| `storage_quota_mb` | integer | No | Storage quota MB |
| `storage_quota_used_mb` | integer | No | Storage used MB |
| `hide_final_grades` | boolean | No | Hide final grades flag |
| `license` | string | No | License info |
| `allow_student_assignment_edits` | boolean | No | Student submission edit allowed |
| `allow_wiki_comments` | boolean | No | Wiki comments allowed |
| `allow_student_forum_attachments` | boolean | No | Forum attachments allowed |
| `open_enrollment` | boolean | No | Open enrollment flag |
| `self_enrollment` | boolean | No | Self enrollment flag |
| `restrict_enrollments_to_course_dates` | boolean | No | Restrict enrollment dates |
| `course_format` | string | No | Course format |
| `access_restricted_by_date` | boolean | No | Date restriction flag |
| `time_zone` | string | No | Timezone name |
| `blueprint` | boolean | Yes | Blueprint course flag |
| `blueprint_restrictions` | object | Yes | Blueprint restrictions |
| `blueprint_restrictions_by_object_type` | object | Yes | Per-object blueprint restrictions |
| `template` | boolean | Yes | Template flag |

### Pydantic Model
```python
from datetime import datetime
from typing import List, Optional, Dict
from pydantic import BaseModel

class Course(BaseModel):
    id: int
    sis_course_id: Optional[str] = None
    uuid: str
    integration_id: Optional[str] = None
    sis_import_id: Optional[int] = None
    name: str
    course_code: str
    original_name: Optional[str] = None
    workflow_state: str
    account_id: int
    root_account_id: int
    enrollment_term_id: int
    grading_periods: Optional[List[dict]] = None
    grading_standard_id: Optional[int] = None
    grade_passback_setting: str
    created_at: datetime
    start_at: Optional[datetime] = None
    end_at: Optional[datetime] = None
    locale: str
    enrollments: Optional[List[dict]] = None
    total_students: Optional[int] = None
    calendar: Optional[dict] = None
    default_view: str
    syllabus_body: Optional[str] = None
    needs_grading_count: Optional[int] = None
    term: Optional[dict] = None
    course_progress: Optional[dict] = None
    apply_assignment_group_weights: bool
    permissions: Optional[Dict[str, bool]] = None
    is_public: bool
    is_public_to_auth_users: bool
    public_syllabus: bool
    public_syllabus_to_auth: bool
    public_description: Optional[str] = None
    storage_quota_mb: int
    storage_quota_used_mb: int
    hide_final_grades: bool
    license: str
    allow_student_assignment_edits: bool
    allow_wiki_comments: bool
    allow_student_forum_attachments: bool
    open_enrollment: bool
    self_enrollment: bool
    restrict_enrollments_to_course_dates: bool
    course_format: str
    access_restricted_by_date: bool
    time_zone: str
    blueprint: Optional[bool] = None
    blueprint_restrictions: Optional[Dict[str, bool]] = None
    blueprint_restrictions_by_object_type: Optional[Dict[str, Dict[str, bool]]] = None
    template: Optional[bool] = None
```

---

## Groups

### Fields
| Field | Type | Nullable? | Description |
|------|------|-----------|-------------|
| `id` | integer | No | Group ID |
| `name` | string | No | Group name |
| `description` | string | Yes | Description |
| `is_public` | boolean | No | Public visibility |
| `followed_by_user` | boolean | No | Following flag |
| `join_level` | string | No | Joining policy |
| `members_count` | integer | No | Members count |
| `avatar_url` | string | Yes | Avatar URL |
| `context_type` | string | No | `"Course"` or `"Account"` |
| `course_id` | integer | Yes | Linked course ID |
| `account_id` | integer | Yes | Linked account ID |
| `role` | string | Yes | Special group role |
| `group_category_id` | integer | No | Parent category ID |
| `storage_quota_mb` | integer | No | Storage quota |

### Pydantic Model
```python
from pydantic import BaseModel
from typing import Optional

class Group(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    is_public: bool
    followed_by_user: bool
    join_level: str
    members_count: int
    avatar_url: Optional[str] = None
    context_type: str
    course_id: Optional[int] = None
    account_id: Optional[int] = None
    role: Optional[str] = None
    group_category_id: int
    storage_quota_mb: int
```

---

## Group Sets (Group Categories)

### Fields
| Field | Type | Nullable? | Description |
|------|------|-----------|-------------|
| `id` | integer | No | Category ID |
| `name` | string | No | Category name |
| `role` | string | Yes | Special category role |
| `self_signup` | string | Yes | Self signup policy |
| `auto_leader` | string | Yes | Auto-leader setting |
| `context_type` | string | No | `"Course"` or `"Account"` |
| `account_id` | integer | Yes | Linked account ID |
| `course_id` | integer | Yes | Linked course ID |
| `group_limit` | integer | Yes | Max group size limit |
| `progress` | object or null | Yes | Background task progress |

### Pydantic Model
```python
from typing import Optional
from pydantic import BaseModel

class GroupCategory(BaseModel):
    id: int
    name: str
    role: Optional[str] = None
    self_signup: Optional[str] = None
    auto_leader: Optional[str] = None
    context_type: str
    account_id: Optional[int] = None
    course_id: Optional[int] = None
    group_limit: Optional[int] = None
    progress: Optional[dict] = None
```

---

## Notes
- All datetime fields are in ISO 8601 format.
- Optional fields are either absent or returned as `null`.
- Canvas API consistently uses `snake_case` field names.
