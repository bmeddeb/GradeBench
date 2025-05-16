# Canvas‑to‑Team Wizard Specification

## 1. Introduction

**Purpose**  
Guide instructors through creating “Team” records in GradeBench by selecting Canvas groups and (optionally) provisioning GitHub repositories and Taiga projects, with manual review at each stage.

**Scope**  
Covers the end‑to‑end wizard UI, the data models involved, field mappings, validation rules, and persistence logic.

## 2. Models Involved

| Model                    | Location                     | Key Fields                                                                            |
|--------------------------|------------------------------|---------------------------------------------------------------------------------------|
| CanvasCourse             | `lms/canvas/models.py`       | `id`, `name`, `course_code`, …                                                        |
| CanvasGroupCategory      | `lms/canvas/models.py`       | `id`, `name`, `canvas_course`                                                         |
| CanvasGroupMembership    | `lms/canvas/models.py`       | `group`, `student`, `is_leader`                                                       |
| Team                     | `core/models.py`             | `id`, `name`, `description`, `github_repo_name`, `taiga_project_name`, …              |
| Student                  | `core/models.py`             | `first_name`, `last_name`, `email`, `student_id`, `canvas_user_id`, `team`            |

## 3. Wizard Workflow

### 3.1 Step 1 – Course Selection

1. **UI**  
   - Dropdown or list of `CanvasCourse` entries.  
   - Two toggles:  
     - ☐ _Associate GitHub repo_  
     - ☐ _Associate Taiga project_

2. **Data**  
   - Selected `course_id`  
   - Boolean flags `use_github`, `use_taiga`  

### 3.2 Step 2 – Group Set Selection

1. **UI**  
   - List of `CanvasGroupCategory` for the chosen course.

2. **Data**  
   - One or more selected `group_category_id` values.

### 3.3 Step 3– Group Selection

1. **UI**  
   - For each selected category, render cards for `CanvasGroup`:  
     - **Card Title:** group name  
     - **Body:** member list (leaders first)  
     - **Footer:** “+” icon to include this group as a Team

2. **Data**  
   - Array of selected `group_id` values  

### 3.4 Step 4 – GitHub Configuration (conditional)

_Only if “Associate GitHub repo” was toggled on in Step 1._

1. **UI**  
   - For each chosen group:  
     - Text input pre‑filled with `{course_code}-{sanitized_group_name}`  
     - Tooltip: “Spaces → `-`, strip invalid chars”  
     - Checkbox “Override template” unlocks editing

2. **Data**  
   - `github_repo_name[group_id]`  

### 3.5 Step 5 – Taiga Configuration (conditional)

_Only if “Associate Taiga project” was toggled on in Step 1._

1. **UI**  
   - Same pattern as Step 4, but for `taiga_project_name[group_id]`

2. **Data**  
   - `taiga_project_name[group_id]`  

### 3.6 Step 6 – Confirmation & Persistence

1. **UI**  
   - Table or cards summarizing for each group:  
     | Team Name | GitHub Repo | Taiga Project |
     |-----------|-------------|---------------|
     | (editable) | (editable) | (editable)    |
   - “Back” ← → “Confirm” buttons

2. **On Confirm**  
   Wrap this in a single transaction per group:

   ```python
   from django.db import transaction

   for group in selected_groups:
       canvas_group = CanvasGroup.objects.get(id=group.id)
       final_name = user_overrides.get(group.id, canvas_group.name)
       final_repo = github_names.get(group.id) or None
       final_project = taiga_names.get(group.id) or None

       with transaction.atomic():
           team, created = Team.objects.update_or_create(
               name=final_name,
               defaults={
                   "description": canvas_group.description or "",
                   "github_repo_name": final_repo,
                   "taiga_project_name": final_project,
                   "canvas_group_id": canvas_group.id,
               }
           )

           memberships = CanvasGroupMembership.objects.filter(group=canvas_group)
           for membership in memberships:
               canvas_user = membership.student
               Student.objects.update_or_create(
                   canvas_user_id=canvas_user.id,
                   defaults={
                       "first_name": canvas_user.first_name,
                       "last_name": canvas_user.last_name,
                       "email": canvas_user.email,
                       "student_id": canvas_user.student_id or "",
                       "team": team,
                   }
               )

           if created:
               messages.success(request, f"Team “{team.name}” created, with {memberships.count()} students.")
           else:
               messages.warning(request, f"Team “{team.name}” updated, students reassigned.")

   return redirect("teams:list")
   ```

3. **Validation & Sanitization**  
   - At least one group selected  
   - Repo/Project names: `^[a-zA-Z0-9\-_]+$`, max length 100  

4. **Error Handling**  
   - Rollback on database errors + generic error message  
   - Prompt override on name collisions  

5. **UI/UX Notes**  
   - Progress bar “Step X of 6”  
   - Back/Next buttons with proper enabling/disabling  
   - Responsive design

## Additional Processes & URL Patterns

Group all auxiliary wizards and batch‑process flows under a dedicated URL namespace, e.g. `/processes/`.  

Example `processes/urls.py`:

```python
# processes/urls.py
from django.urls import path
from .views import TeamWizard, IdentityReconcileWizard, GitHubBatchCreateView

app_name = "processes"
urlpatterns = [
    path('teams/', TeamWizard.as_view(), name='teams'),
    path('identity-reconcile/', IdentityReconcileWizard.as_view(), name='identity_reconcile'),
    path('github-batch/', GitHubBatchCreateView.as_view(), name='github_batch_create'),
    # other flows...
]
```

Then users access:

- `/processes/teams/`
- `/processes/identity-reconcile/`
- `/processes/github-batch/`

This keeps all one‑off wizards and batch processes organized and discoverable.
