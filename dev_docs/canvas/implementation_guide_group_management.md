# Canvas Group Management Methods Implementation Guide

This document outlines the implementation of Canvas group management methods and how to test them.

## Implemented Methods

We've added the following methods to the Canvas Client class to support group management create and update operations:

1. `create_group_category` - Creates a new group category (group set) in a course
2. `update_group_category` - Updates an existing group category
3. `create_group` - Creates a new group within a group category
4. `update_group` - Updates an existing group
5. `set_group_members` - Sets the members of a group (overwrites existing members)

## Method Details

### Create Group Category

```python
async def create_group_category(
    self, course_id: int, name: str, self_signup: Optional[str] = None,
    auto_leader: Optional[str] = None, group_limit: Optional[int] = None
):
```

**Parameters:**
- `course_id`: Canvas course ID
- `name`: The name of the group category
- `self_signup`: "enabled" or "restricted" - whether students can sign up for a group themselves
- `auto_leader`: "first" or "random" - assigns group leader automatically
- `group_limit`: Maximum number of members per group

### Update Group Category

```python
async def update_group_category(
    self, category_id: int, name: Optional[str] = None, self_signup: Optional[str] = None,
    auto_leader: Optional[str] = None, group_limit: Optional[int] = None
):
```

**Parameters:**
- `category_id`: Canvas group category ID
- `name`: The name of the group category
- `self_signup`: "enabled" or "restricted" - whether students can sign up for a group themselves
- `auto_leader`: "first" or "random" - assigns group leader automatically
- `group_limit`: Maximum number of members per group

### Create Group

```python
async def create_group(
    self, category_id: int, name: str, description: Optional[str] = None
):
```

**Parameters:**
- `category_id`: Canvas group category ID
- `name`: The name of the group
- `description`: Optional description of the group

### Update Group

```python
async def update_group(
    self, group_id: int, name: Optional[str] = None, description: Optional[str] = None,
    members: Optional[List[int]] = None
):
```

**Parameters:**
- `group_id`: Canvas group ID
- `name`: The name of the group
- `description`: Description of the group
- `members`: List of user IDs to set as members (overwrites existing members)

### Set Group Members

```python
async def set_group_members(
    self, group_id: int, user_ids: List[int]
):
```

**Parameters:**
- `group_id`: Canvas group ID
- `user_ids`: List of user IDs to set as members (overwrites existing members)

## Synchronous Utility Functions

To address issues with mixing asynchronous and synchronous code in Django views, we've implemented synchronous utility functions in `sync_utils.py` that use the standard `requests` library instead of the async `httpx` client:

### Group Category (Group Set) Management

```python
def create_group_category_sync(
    integration, course_id, name, self_signup=None, auto_leader=None, group_limit=None
)
```

```python
def update_group_category_sync(
    integration, category_id, name=None, self_signup=None, auto_leader=None, group_limit=None
)
```

```python
def delete_group_category_sync(
    integration, category_id
)
```

### Group Management

```python
def create_group_sync(
    integration, category_id, name, description=None
)
```

```python
def update_group_sync(
    integration, group_id, name=None, description=None, members=None
)
```

```python
def delete_group_sync(
    integration, group_id
)
```

### Group Membership Management

```python
def push_group_memberships_sync(
    integration, group_id, user_ids
)
```

```python
def push_all_group_memberships_sync(
    integration, course_id
)
```

## Testing

To test these methods, you can use the Django shell with the following steps:

1. Start the Django shell:
```
python manage.py shell
```

2. Import necessary modules:
```python
import asyncio
from lms.canvas.models import CanvasIntegration
from lms.canvas.client import Client
```

3. Get an integration instance and create a client:
```python
integration = CanvasIntegration.objects.first()
client = Client(integration)
```

4. Test creating a group category:
```python
async def test_create_category():
    result = await client.create_group_category(
        course_id=11921869,  # Replace with actual course ID
        name="Test Category",
        self_signup="enabled",
        group_limit=4
    )
    print(f"Created category: {result}")
    return result

category = asyncio.run(test_create_category())
category_id = category['id']
```

5. Test creating a group in the category:
```python
async def test_create_group(category_id):
    result = await client.create_group(
        category_id=category_id,
        name="Test Group",
        description="Test group created via API"
    )
    print(f"Created group: {result}")
    return result

group = asyncio.run(test_create_group(category_id))
group_id = group['id']
```

6. Test setting group members:
```python
async def test_set_members(group_id):
    result = await client.set_group_members(
        group_id=group_id,
        user_ids=[123456, 789012]  # Replace with actual user IDs
    )
    print(f"Set members: {result}")
    return result

updated_members = asyncio.run(test_set_members(group_id))
```

## Usage in Views

These asynchronous methods were originally integrated into the views, but this caused issues with group memberships not being properly saved to Canvas because the async operations were cut off prematurely when the view function returned.

To solve this issue, we now use the synchronous utility functions:

1. `create_group_set` view now uses `create_group_category_sync`
2. `edit_group_set` view now uses `update_group_category_sync`
3. `delete_group_set` view now uses `delete_group_category_sync`
4. `create_group` view now uses `create_group_sync`
5. `edit_group` view now uses `update_group_sync`
6. `delete_group` view now uses `delete_group_sync`

For student group assignments, we use:
1. `add_student_to_group` view now includes a call to `push_group_memberships_sync`
2. `remove_student_from_group` view now includes a call to `push_group_memberships_sync`
3. `batch_assign_students` view now includes a call to `push_group_memberships_sync` for each modified group
4. `random_assign_students` view now includes a call to `push_group_memberships_sync` for each modified group

We've also added a dedicated view and endpoint for pushing all group memberships to Canvas:
- `push_course_group_memberships` view uses `push_all_group_memberships_sync`

## Problem Resolution

The original implementation mixed asynchronous and synchronous code in Django views, which caused issues with assignments not being pushed to Canvas properly. The asynchronous operations would be initiated but not fully completed before the view returned.

The synchronous approach ensures that:
1. API calls complete fully before the view returns a response
2. Database and Canvas states remain consistent
3. Group membership assignments are properly pushed to Canvas

This change fixed the issue where group assignments would show up in the local database but not in Canvas, ensuring that both systems stay in sync.