# Separation of Concerns: Pydantic vs. Django ORM

This document outlines best practices for integrating Pydantic models alongside your existing Django ORM models when syncing data from the Canvas LMS API.

---

## 1. Why Separate Pydantic from Django Models?

* **Clear Responsibilities**:

  * **Pydantic models** handle JSON parsing, validation, and type conversion at the API boundary.
  * **Django models** manage database schema, migrations, and persistence logic.
* **Avoid Tight Coupling**:

  * Django ORM fields (`CharField`, `DateTimeField`, etc.) do not map one-to-one to Pydantic features.
  * Mixing the two can create confusion around validation, defaults, and migrations.

---

## 2. Pydantic at the API Boundary

Define Pydantic schemas to mirror Canvas API JSON responses. Keep them in a separate module (e.g., `canvas/schemas.py`):

```python
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel

class Course(BaseModel):
    id: int
    name: str
    course_code: str
    start_at: Optional[datetime]
    end_at: Optional[datetime]
    # ... other fields as needed

class Enrollment(BaseModel):
    id: int
    user_id: int
    role: str
    # ...
```

* **Validation**: Ensures dates, enums, and required fields are correct before hitting your database.
* **Autocompletion**: Downstream code editors will offer field names and types.

---

## 3. Django Models for Persistence

Your existing Django models remain untouched and focused on database concerns:

```python
from django.db import models

class CanvasCourse(models.Model):
    canvas_id    = models.IntegerField(unique=True)
    name         = models.CharField(max_length=255)
    course_code  = models.CharField(max_length=50)
    start_at     = models.DateTimeField(null=True, blank=True)
    end_at       = models.DateTimeField(null=True, blank=True)
    # ...
```

* **Migrations**: Handled by Django’s `makemigrations` and `migrate`.
* **Querying**: Use familiar ORM APIs (`.filter()`, `.update_or_create()`).

---

## 4. Typical Sync Flow

1. **Fetch & Validate**

   ```python
   raw = await canvas_client._get_all("/api/v1/courses")
   courses = [Course.parse_obj(r) for r in raw]
   ```
2. **Persist**

   ```python
   for course in courses:
       CanvasCourse.objects.update_or_create(
           canvas_id=course.id,
           defaults={
               'name': course.name,
               'course_code': course.course_code,
               'start_at': course.start_at,
               'end_at': course.end_at,
           }
       )
   ```

This clear two‑step process keeps HTTP parsing separate from database writes.

---

## 5. When to Add Pydantic for Django Models

Only if you’re exposing your own API (e.g., via FastAPI) and need to serialize Django instances back to JSON. In that case:

1. Define a Pydantic model for your API output.
2. Use a converter (`from_django`) or a library like `django-pydantic` to map fields.
3. Keep this as a distinct layer in your codebase.

Example:

```python
class CourseOut(BaseModel):
    id: int
    name: str
    course_code: str

    @classmethod
    def from_django(cls, instance: CanvasCourse) -> "CourseOut":
        return cls(
            id=instance.canvas_id,
            name=instance.name,
            course_code=instance.course_code,
        )
```

---

## 6. Conclusion

* **Pydantic** → Use for **parsing & validating** external API JSON.
* **Django ORM** → Use for **schema definition** and **persistence**.
* **Syncer** service → Maps validated Pydantic DTOs into Django models via `update_or_create()`.

This layering ensures maintainability, testability, and a clear separation of concerns.
