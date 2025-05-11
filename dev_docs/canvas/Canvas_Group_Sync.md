# Canvas Group Sync — End‑to‑End Steps

Follow these steps to fetch students and their Canvas groups, mapping them into your existing `Team` and `Student.team` fields — while preserving manually created Teams when educators have not set up Canvas groups.

---

## 1. Update Your Django Models

1. **Extend `Team`**

   Add Canvas fields so each Team maps to a Canvas group:

   ```diff
   # lms/canvas/models.py

   class Team(models.Model, AsyncModelMixin):
       # … existing fields …

       canvas_course   = models.ForeignKey(
           CanvasCourse,
           on_delete=models.CASCADE,
           related_name="teams",
           null=True, blank=True,
       )
       canvas_group_id = models.PositiveIntegerField(
           null=True, blank=True, db_index=True,
           help_text="Canvas /api/v1/groups/:id"
       )
       last_synced_at = models.DateTimeField(
           null=True, blank=True,
           help_text="When this team was last synced with Canvas"
       )

       class Meta:
           # Add compound index for better performance when querying teams by course
           indexes = [
               models.Index(fields=['canvas_course', 'canvas_group_id'])
           ]
   ```

2. **Link `CanvasEnrollment` → `Student`** *(optional but recommended)*:

   ```diff
   # lms/canvas/models.py

   class CanvasEnrollment(models.Model):
       # … existing fields …

       student = models.ForeignKey(
           'core.Student',
           on_delete=models.SET_NULL,
           null=True, blank=True,
           related_name='canvas_enrollments'
       )
   ```

3. **Run migrations**:

   ```bash
   python manage.py makemigrations lms
   python manage.py migrate
   ```

---

## 2. Extend Your CanvasClient

Add async methods to fetch groups and memberships:

```python
class CanvasClient:
    # … existing methods …

    async def get_group_categories(self, course_id: int) -> List[Dict]:
        return await self.request(
            'GET', f'courses/{course_id}/group_categories', params={'per_page': 100}
        )

    async def get_groups(self, category_id: int) -> List[Dict]:
        return await self.request(
            'GET', f'group_categories/{category_id}/groups', params={'per_page': 100}
        )

    async def get_group_members(self, group_id: int) -> List[Dict]:
        return await self.request(
            'GET', f'groups/{group_id}/users', params={'per_page': 100}
        )
```

---

## 3. Create Sync Routines

In your sync service (e.g. `CanvasSyncer`), add:

```python
from django.utils import timezone
from lms.canvas.models import CanvasCourse, CanvasEnrollment
from core.models import Student, Team
import logging

logger = logging.getLogger(__name__)

class CanvasSyncer:
    # … existing sync_course …

    async def sync_canvas_groups(self, course: CanvasCourse, user_id=None):
        """Sync Canvas groups for a course to Teams"""
        from .progress import SyncProgress

        if user_id:
            await SyncProgress.async_update(
                user_id, course.canvas_id,
                status="fetching_groups",
                message="Fetching group categories from Canvas..."
            )

        # 1. Fetch group‑sets
        categories = await self.client.get_group_categories(course.canvas_id)

        # Track all Canvas group IDs to handle cleanup later
        current_group_ids = []

        # 2. Upsert Teams for each Canvas group
        for cat in categories:
            if user_id:
                await SyncProgress.async_update(
                    user_id, course.canvas_id,
                    status="fetching_groups",
                    message=f"Fetching groups in category: {cat.get('name', 'Unnamed Category')}"
                )

            groups = await self.client.get_groups(cat['id'])

            if user_id and groups:
                await SyncProgress.async_update(
                    user_id, course.canvas_id,
                    status="saving_groups",
                    message=f"Saving {len(groups)} groups to database..."
                )

            for grp in groups:
                current_group_ids.append(grp['id'])

                # Update or create team with timestamp
                team, created = Team.objects.update_or_create(
                    canvas_group_id=grp['id'],
                    canvas_course=course,
                    defaults={
                        'name': grp.get('name')[:100],
                        'description': grp.get('description','')[:500],
                        'last_synced_at': timezone.now()
                    }
                )

                # Log when new teams are created
                if created and logger:
                    logger.info(f"Created new team from Canvas group: {team.name} (ID: {grp['id']})")

        # Return group IDs for potential cleanup
        return current_group_ids

    async def sync_group_memberships(self, course: CanvasCourse, user_id=None):
        """Sync group memberships to Student.team assignments"""
        from .progress import SyncProgress

        # 3. Assign students to teams based on membership
        teams = Team.objects.filter(canvas_course=course, canvas_group_id__isnull=False)

        if user_id:
            await SyncProgress.async_update(
                user_id, course.canvas_id,
                status="syncing_members",
                message=f"Syncing memberships for {teams.count()} teams..."
            )

        for i, team in enumerate(teams):
            if not team.canvas_group_id:
                continue  # Skip manually created teams

            if user_id and i > 0 and i % 5 == 0:
                await SyncProgress.async_update(
                    user_id, course.canvas_id,
                    status="syncing_members",
                    message=f"Syncing team {i+1} of {teams.count()}: {team.name}"
                )

            try:
                members = await self.client.get_group_members(team.canvas_group_id)

                for m in members:
                    try:
                        enroll = CanvasEnrollment.objects.get(canvas_id=m['id'], course=course)
                    except CanvasEnrollment.DoesNotExist:
                        if logger:
                            logger.warning(
                                f"Enrollment not found for user ID {m['id']} in team {team.name}"
                            )
                        continue

                    # Link or create Student, then assign team
                    student = enroll.student
                    if not student:
                        # Handle potential missing data with safe defaults
                        try:
                            user_name_parts = enroll.user_name.split()
                            first_name = user_name_parts[0] if user_name_parts else "Unknown"
                            last_name = " ".join(user_name_parts[1:]) if len(user_name_parts) > 1 else ""

                            student, created = Student.objects.update_or_create(
                                canvas_user_id=str(enroll.user_id),
                                defaults={
                                    'email': enroll.email or f"canvas-user-{enroll.user_id}@example.com",
                                    'first_name': first_name,
                                    'last_name': last_name,
                                }
                            )

                            if created and logger:
                                logger.info(f"Created new student from Canvas enrollment: {student.full_name}")

                            enroll.student = student
                            enroll.save(update_fields=['student'])
                        except Exception as e:
                            if logger:
                                logger.error(f"Error creating student for enrollment {enroll.id}: {str(e)}")
                            continue

                    # Only update if team has changed
                    if student.team != team:
                        old_team = student.team
                        student.team = team
                        student.save(update_fields=['team'])

                        if logger:
                            logger.info(
                                f"Updated student {student.full_name} team assignment: " +
                                f"{old_team.name if old_team else 'None'} → {team.name}"
                            )
            except Exception as e:
                if logger:
                    logger.error(f"Error syncing memberships for team {team.name}: {str(e)}")
                continue
```

---

## 4. Wire into Your Full Sync

After your `sync_course` call, invoke the group sync with progress tracking:

```python
# Add to sync_course method
if user_id:
    await SyncProgress.async_update(
        user_id, course_id, current=9, total=10,
        status="syncing_groups",
        message="Syncing Canvas groups and team memberships..."
    )

# Sync groups and get current group IDs for cleanup
current_group_ids = await self.sync_canvas_groups(course, user_id)
await self.sync_group_memberships(course, user_id)

# Optional: Clean up teams no longer in Canvas
# Team.objects.filter(canvas_course=course,
#                    canvas_group_id__isnull=False)
#                   .exclude(canvas_group_id__in=current_group_ids)
#                   .delete()
```

* **Imported Teams**: have `canvas_group_id` set.
* **Manual Teams**: created by educators will have `canvas_group_id = null`.

Canvas sync routines only touch Teams with a non‑null `canvas_group_id`, leaving manual Teams and their student assignments intact when Canvas returns no groups.

---

## 5. Manual Teams & Fallback Logic

* **Detect absence of Canvas groups**: if `get_group_categories` returns an empty list, skip calls to `sync_canvas_groups` and `sync_group_memberships`.
* **Preserve manual Teams**: manual Teams (no `canvas_group_id`) remain available for students to be assigned manually in your UI.
* **UI hint**: when Canvas has no groups, show a banner like "No Canvas groups found — please create Teams manually."
* **Visual differentiation**: Add a Canvas icon or badge to Canvas-synced teams in your UI to distinguish them from manually created teams.
* **Clean‐up policy**: optionally, you can delete previously imported Teams if Canvas categories vanish, by filtering `Team.objects.filter(canvas_course=course, canvas_group_id__isnull=False).exclude(canvas_group_id__in=current_group_ids).delete()`.

---

## 6. Querying Results

Retrieve students with their teams (whether imported or manual):

```python
from core.models import Student

students = Student.objects.select_related('team').all()
for s in students:
    print(s.full_name, '→', s.team.name if s.team else 'No team')

# Distinguish canvas vs. manual teams
for s in students:
    if s.team:
        team_source = "Canvas" if s.team.canvas_group_id else "Manual"
        print(f"{s.full_name} → {s.team.name} ({team_source})")
```

In DRF serializers:

```python
class StudentSerializer(serializers.ModelSerializer):
    team = serializers.CharField(source='team.name', default=None)
    team_source = serializers.SerializerMethodField()

    class Meta:
        model = Student
        fields = ['id', 'full_name', 'team', 'team_source', ...]

    def get_team_source(self, obj):
        if obj.team and obj.team.canvas_group_id:
            return 'canvas'
        elif obj.team:
            return 'manual'
        return None


## 5. Manual Teams & Fallback Logic

* **Detect absence of Canvas groups**: if `get_group_categories` returns an empty list, skip calls to `sync_canvas_groups` and `sync_group_memberships`.
* **Preserve manual Teams**: manual Teams (no `canvas_group_id`) remain available for students to be assigned manually in your UI.
* **UI hint**: when Canvas has no groups, show a banner like “No Canvas groups found — please create Teams manually.”
* **Clean‐up policy**: optionally, you can delete previously imported Teams if Canvas categories vanish, by filtering `Team.objects.filter(canvas_course=course, canvas_group_id__isnull=False).exclude(canvas_group_id__in=current_ids).delete()`.

---

## 6. Querying Results

Retrieve students with their teams (whether imported or manual):

```python
from core.models import Student

students = Student.objects.select_related('team').all()
for s in students:
    print(s.full_name, '→', s.team.name if s.team else 'No team')
```

In DRF serializers:

```python
team = serializers.CharField(source='team.name', default=None)
```

---

## 7. Pushing Team Assignments to Canvas

Canvas provides group membership APIs so you can mirror your application’s Teams back into Canvas.

### 7.1 Invite Individual Students to a Group

```http
POST /api/v1/groups/:group_id/invite
Content-Type: application/x-www-form-urlencoded

invitees[]=<canvas_user_id>&invitees[]=<canvas_user_id>&...
```

Invites the specified users into the group (or auto‑joins them if the group’s `join_level` is `parent_context_auto_join`).

### 7.2 Overwrite a Group’s Membership

```http
PUT /api/v1/groups/:group_id
Content-Type: application/x-www-form-urlencoded

members[]=<canvas_user_id>&members[]=<canvas_user_id>&...
```

Passing the complete list of user IDs will sync Canvas—adding missing users and removing any that aren’t in your list.

### 7.3 Bulk‑assign Unassigned Members

```http
POST /api/v1/group_categories/:group_category_id/assign_unassigned_members?sync=true
```

Evenly distributes any users not already in a group of that category across existing groups. Great for filling out teams automatically.

### 7.4 CanvasClient Methods

Extend your `CanvasClient` with these helpers:

```python
class CanvasClient:
    # … existing methods …

    async def invite_user_to_group(self, group_id: int, user_ids: List[int]):
        return await self.request(
            'POST', f'groups/{group_id}/invite',
            data={'invitees[]': user_ids}
        )

    async def set_group_members(self, group_id: int, user_ids: List[int]):
        return await self.request(
            'PUT', f'groups/{group_id}',
            data=[('members[]', uid) for uid in user_ids]
        )

    async def assign_unassigned(self, category_id: int, sync: bool = True):
        params = {'sync': 'true'} if sync else {}
        return await self.request(
            'POST', f'group_categories/{category_id}/assign_unassigned_members',
            params=params
        )
```

### 7.5 Syncer Method to Push Assignments

In your `CanvasSyncer`, add a method to push local `Team` → Canvas group assignments:

```python
async def push_group_assignments(self, course: CanvasCourse):
    from lms.canvas.models import CanvasEnrollment
    # For each imported Team, gather current members and send to Canvas
    for team in Team.objects.filter(canvas_course=course, canvas_group_id__isnull=False):
        user_ids = [int(enroll.user_id)
                    for enroll in CanvasEnrollment.objects.filter(student__team=team)]
        await self.client.set_group_members(team.canvas_group_id, user_ids)
```

This ensures your local `Team` and `Student.team` relationships are reflected back into Canvas’s group structure.
