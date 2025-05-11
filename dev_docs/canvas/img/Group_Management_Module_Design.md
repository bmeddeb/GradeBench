# Canvas Group Management Module Design

## Overview

This document outlines the design for a Canvas group management module within GradeBench's LMS app. The module will mirror Canvas's native group management functionality, allowing instructors to create, modify, and manage group sets (categories) and groups, as well as assign students to groups.

## Goals

- Mirror Canvas's group management UI and workflow
- Enable instructors to manage group sets and groups without leaving GradeBench
- Provide bidirectional sync with Canvas
- Support manual assignment of students to groups
- Maintain data consistency between GradeBench and Canvas

## Canvas Group Structure

In Canvas, groups are organized as follows:

1. **Group Sets** (Categories): Collections of groups within a course. Each group set has properties like:
   - Name
   - Self-signup settings (enabled/disabled)
   - Group member limits
   - Student group assignment method

2. **Groups**: Individual groups within a group set. Each group has:
   - Name
   - Description
   - Member list

3. **Group Memberships**: Assignments of students to specific groups

## Current Implementation State

GradeBench already has models that mirror Canvas's structure:

- `CanvasGroupCategory` (Group Set)
- `CanvasGroup` (Group)
- `CanvasGroupMembership` (Student membership in a group)
- Syncing functionality via `CanvasSyncer` (pull data from Canvas)
- Push functionality to update Canvas with local changes

## UI Design

### 1. Group Management Tab

Add a "Groups" tab to the Canvas course dashboard that shows group sets and allows management:


### 2. Main Components

#### Group Sets List View
- Display all group sets for the course in a tabbed interface (similar to Canvas)
- Each tab represents a group set
- Show group set details (name, settings, description)
- Provide actions: Edit, Delete, Add Group, Random Assignment

#### Groups Panel
- Display all groups within the selected group set
- Show group name, description, and member count
- Provide actions: Edit, Delete, View Members

#### Students Panel
- Display students in the course
- Show unassigned students separately
- Drag-and-drop interface for assigning students to groups
- Search and filter options for finding students

### 3. Functionality

#### Group Set Management
- Create new group sets
- Edit group set properties:
  - Name
  - Self-signup settings
  - Group limit
  - Leader assignment
- Delete group sets (with confirmation)

#### Group Management
- Create new groups within a set
- Edit group properties:
  - Name
  - Description
- Delete groups (with confirmation)
- View group members

#### Student Assignment
- Manually assign students to groups via drag-and-drop
- Random assignment of unassigned students
- Move students between groups
- Remove students from groups

#### Sync Controls
- Sync button to pull latest data from Canvas
- Push button to update Canvas with local changes
- Sync status indicator
- Last sync timestamp display

## Technical Design

### 1. Data Models

We'll use the existing models:

```python
class CanvasGroupCategory(models.Model, AsyncModelMixin):
    """Represents a Canvas Group Category/Group Set"""
    canvas_id = models.PositiveIntegerField(unique=True)
    course = models.ForeignKey(CanvasCourse, on_delete=models.CASCADE, related_name="group_categories")
    name = models.CharField(max_length=255)
    self_signup = models.CharField(max_length=50, null=True, blank=True)
    auto_leader = models.CharField(max_length=50, null=True, blank=True)
    group_limit = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(auto_now=True)
    
class CanvasGroup(models.Model, AsyncModelMixin):
    """Represents a Canvas Group within a Group Category"""
    canvas_id = models.PositiveIntegerField(unique=True)
    category = models.ForeignKey(CanvasGroupCategory, on_delete=models.CASCADE, related_name="groups")
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    last_synced_at = models.DateTimeField(auto_now=True)
    core_team = models.OneToOneField("core.Team", on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name="canvas_group_link")
    
class CanvasGroupMembership(models.Model, AsyncModelMixin):
    """Represents a student's membership in a Canvas Group"""
    group = models.ForeignKey(CanvasGroup, on_delete=models.CASCADE, related_name="memberships")
    user_id = models.PositiveIntegerField()  # Canvas user ID
    student = models.ForeignKey("core.Student", on_delete=models.SET_NULL, null=True, blank=True, 
                                related_name="canvas_group_memberships")
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)
```

### 2. API Endpoints

We'll need to create new API endpoints for the group management UI:

```python
# Group Sets endpoints
GET /api/canvas/courses/{course_id}/group_sets/  # List all group sets for a course
POST /api/canvas/courses/{course_id}/group_sets/  # Create a new group set
GET /api/canvas/group_sets/{group_set_id}/  # Get details for a group set
PUT /api/canvas/group_sets/{group_set_id}/  # Update a group set
DELETE /api/canvas/group_sets/{group_set_id}/  # Delete a group set

# Groups endpoints
GET /api/canvas/group_sets/{group_set_id}/groups/  # List all groups in a set
POST /api/canvas/group_sets/{group_set_id}/groups/  # Create a new group
GET /api/canvas/groups/{group_id}/  # Get details for a group
PUT /api/canvas/groups/{group_id}/  # Update a group
DELETE /api/canvas/groups/{group_id}/  # Delete a group

# Group Membership endpoints
GET /api/canvas/groups/{group_id}/members/  # List all members in a group
POST /api/canvas/groups/{group_id}/members/  # Add a member to a group
DELETE /api/canvas/groups/{group_id}/members/{user_id}/  # Remove a member from a group

# Sync endpoints
POST /api/canvas/courses/{course_id}/sync_groups/  # Pull latest group data from Canvas
POST /api/canvas/courses/{course_id}/push_groups/  # Push group data to Canvas
```

### 3. View Architecture

#### Django Views

```python
# Group Sets views
class GroupSetListView(View):
    """List all group sets for a course"""
    
class GroupSetDetailView(View):
    """Get, update, or delete a group set"""
    
class GroupSetCreateView(View):
    """Create a new group set"""

# Groups views
class GroupListView(View):
    """List all groups in a set"""
    
class GroupDetailView(View):
    """Get, update, or delete a group"""
    
class GroupCreateView(View):
    """Create a new group"""

# Group Membership views
class GroupMembershipView(View):
    """Manage group memberships"""
    
# Sync views
class SyncGroupsView(View):
    """Sync groups with Canvas"""
    
class PushGroupsView(View):
    """Push group changes to Canvas"""
```

#### Templates

```
- templates/
  - canvas/
    - groups/
      - index.html  # Main group management page
      - group_set_list.html  # List of group sets
      - group_set_detail.html  # Group set details
      - group_form.html  # Form for creating/editing groups
      - group_set_form.html  # Form for creating/editing group sets
```

### 4. Frontend Components

We'll use a combination of Django templates and JavaScript for the UI:

#### JavaScript Components

```javascript
// Group Set Tab Component
const GroupSetTabs = {
    init: function() {
        // Initialize tabs for group sets
    },
    switchTab: function(groupSetId) {
        // Switch to the selected group set tab
    }
};

// Group List Component
const GroupList = {
    init: function(groupSetId) {
        // Initialize list of groups for a group set
    },
    loadGroups: function(groupSetId) {
        // Load groups via AJAX
    }
};

// Drag-and-Drop Component
const DragDropAssign = {
    init: function() {
        // Initialize drag-and-drop for student assignment
    },
    handleDrop: function(studentId, groupId) {
        // Handle student assignment via AJAX
    }
};

// Sync Component
const GroupSync = {
    syncFromCanvas: function(courseId) {
        // Trigger sync from Canvas
    },
    pushToCanvas: function(courseId) {
        // Trigger push to Canvas
    }
};
```

### 5. API Implementation

#### Group Sets API

```python
from django.http import JsonResponse
from lms.canvas.models import CanvasCourse, CanvasGroupCategory
from lms.canvas.client import Client

class GroupSetsAPIView(View):
    async def get(self, request, course_id):
        # Get all group sets for a course
        course = await CanvasCourse.objects.aget(canvas_id=course_id)
        group_sets = await CanvasGroupCategory.objects.filter(course=course).order_by('name').aall()
        
        return JsonResponse({
            'group_sets': [
                {
                    'id': gs.canvas_id,
                    'name': gs.name,
                    'self_signup': gs.self_signup,
                    'group_limit': gs.group_limit,
                    'auto_leader': gs.auto_leader,
                    'created_at': gs.created_at,
                    'group_count': await gs.groups.acount(),
                }
                for gs in group_sets
            ]
        })
    
    async def post(self, request, course_id):
        # Create a new group set
        # This will create in our DB and then push to Canvas
        data = json.loads(request.body)
        course = await CanvasCourse.objects.aget(canvas_id=course_id)
        
        # Get Canvas integration and create client
        integration = await CanvasIntegration.objects.afirst()
        client = Client(integration)
        
        # Create group set in Canvas
        canvas_data = await client.request(
            'POST', 
            f'courses/{course_id}/group_categories',
            data={
                'name': data['name'],
                'self_signup': data.get('self_signup'),
                'group_limit': data.get('group_limit'),
                'auto_leader': data.get('auto_leader'),
            }
        )
        
        # Save to our database
        group_set = await client._save_group_category(canvas_data, course)
        
        return JsonResponse({
            'success': True,
            'group_set': {
                'id': group_set.canvas_id,
                'name': group_set.name,
                # Other fields...
            }
        })
```

Similar implementations for other API endpoints...

## Syncing Strategy

### Pull from Canvas

1. Fetch all group categories (sets) from Canvas API
2. Fetch all groups for each category
3. Fetch all members for each group
4. Update local database models
5. Link students to groups based on Canvas user IDs

### Push to Canvas

1. For each modified group set, push changes to Canvas
2. For each modified group, push changes to Canvas
3. For each modified membership, push changes to Canvas

## Incremental Development Plan

### Phase 1: Read-Only View
- Implement the UI for viewing group sets and groups
- Display students assigned to each group
- Show sync status and last sync time

### Phase 2: Group Management
- Implement creation, editing, and deletion of group sets
- Implement creation, editing, and deletion of groups
- Add manual sync button to pull latest data from Canvas

### Phase 3: Student Assignment
- Implement drag-and-drop interface for student assignment
- Add functionality to move students between groups
- Implement random assignment of unassigned students

### Phase 4: Full Sync
- Implement bidirectional sync with Canvas
- Add push button to update Canvas with local changes
- Add sync status indicators and error handling

## UI Mockups

### Group Management Main View

```
+------------------------------------+
| Course: CS101                      |
+------------------------------------+
| Dashboard | People | Groups | ... |
+------------------------------------+
| Group Sets:                        |
| [Project Teams] [Lab Partners] ... |
+------------------------------------+
| Project Teams                      |
|                                    |
| + New Group  Random Assign  Sync   |
|                                    |
| +------------+ +------------+      |
| | Team Alpha | | Team Beta  |      |
| |            | |            |      |
| | • John D   | | • Alice W  |      |
| | • Sarah M  | | • Bob T    |      |
| | • Mike P   | | • Carol R  |      |
| |            | |            |      |
| | [Edit]     | | [Edit]     |      |
| +------------+ +------------+      |
|                                    |
| Unassigned Students:               |
| • David K                          |
| • Emma J                           |
+------------------------------------+
```

### Group Edit Form

```
+------------------------------------+
| Edit Group                         |
+------------------------------------+
| Name: [Team Alpha_____________]    |
|                                    |
| Description:                       |
| [A team focused on frontend dev__] |
| [_______________________________]  |
|                                    |
| Members:                           |
| [x] John D                         |
| [x] Sarah M                        |
| [x] Mike P                         |
| [ ] David K                        |
| [ ] Emma J                         |
|                                    |
| [Cancel]           [Save Changes]  |
+------------------------------------+
```