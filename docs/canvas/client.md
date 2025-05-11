# Canvas Client Design and Methods

The Canvas client in the GradeBench application is designed as an asynchronous API client that interacts with the Canvas LMS API. It uses `httpx` for making HTTP requests and provides methods for various Canvas operations.

## Core Design

1. **Async Architecture**: Uses Python's async/await pattern for non-blocking API calls
2. **Integration-based**: Initialized with a CanvasIntegration instance that contains the API key and base URL
3. **Pagination Handling**: Automatically handles Canvas API pagination for large result sets
4. **Sync/Async Bridge**: Uses `sync_to_async` for ORM operations within async functions

## Main Methods

### HTTP Request Method
- `async def request(method, endpoint, params, data)`: Core method that handles all API requests

### Course Methods
- `async def get_courses()`: Get all courses for the authenticated user
- `async def get_course(course_id)`: Get a single course by ID
- `async def sync_course(course_id, user_id)`: Sync a course and its enrollments, assignments, and submissions
- `async def sync_all_courses(user_id)`: Sync all available courses

### Enrollment Methods
- `async def get_enrollments(course_id)`: Get all enrollments for a course
- `async def get_course_users(course_id)`: Get all users with detailed information

### Assignment and Submission Methods
- `async def get_assignments(course_id)`: Get all assignments for a course
- `async def get_assignment(course_id, assignment_id)`: Get a single assignment by ID
- `async def get_submissions(course_id, assignment_id)`: Get all submissions for an assignment
- `async def get_submission(course_id, assignment_id, user_id)`: Get a submission for a specific user

### Group Management Methods
- `async def get_group_categories(course_id)`: Get all group categories for a course
- `async def get_groups(category_id)`: Get all groups for a category
- `async def get_group_members(group_id)`: Get all members for a group
- `async def invite_user_to_group(group_id, user_ids)`: Invite users to a group
- `async def set_group_members(group_id, user_ids)`: Set the members of a group (overwrites existing members)
- `async def assign_unassigned(category_id, sync)`: Randomly assign unassigned students to groups
- `async def create_group_category(course_id, name, self_signup, auto_leader, group_limit)`: Create a new group category in a course
- `async def update_group_category(category_id, name, self_signup, auto_leader, group_limit)`: Update an existing group category
- `async def create_group(category_id, name, description)`: Create a new group in a category
- `async def update_group(group_id, name, description, members)`: Update an existing group

### Database Save Methods
- `_save_course(course_data)`: Save course data to the database
- `_save_enrollment(enrollment_data, course)`: Save enrollment data to the database
- `_save_assignment(assignment_data, course)`: Save assignment data to the database
- `_save_submission(submission_data, assignment)`: Save submission data to the database
- `_save_group_category(category_data, course)`: Save group category data to the database
- `_save_group(group_data, category)`: Save group data to the database
- `_save_group_membership(member_data, group)`: Save group membership data to the database

## Integration with CanvasSyncer

The client works together with the CanvasSyncer class for higher-level synchronization operations:

1. **Sync Canvas Groups to Teams**: Import Canvas groups as Teams in the application
2. **Sync Group Memberships**: Import Canvas group memberships to Student.team assignments
3. **Push Group Assignments**: Push local Team assignments back to Canvas groups

## Synchronous Utility Functions (sync_utils.py)

To avoid issues with mixing asynchronous and synchronous code in views, we provide synchronous versions of the key group management operations:

### Group Category (Group Set) Management
- `create_group_category_sync(integration, course_id, name, self_signup, auto_leader, group_limit)`: Create a group category in Canvas synchronously
- `update_group_category_sync(integration, category_id, name, self_signup, auto_leader, group_limit)`: Update a group category in Canvas synchronously
- `delete_group_category_sync(integration, category_id)`: Delete a group category from Canvas synchronously

### Group Management
- `create_group_sync(integration, category_id, name, description)`: Create a group in Canvas synchronously
- `update_group_sync(integration, group_id, name, description, members)`: Update a group in Canvas synchronously
- `delete_group_sync(integration, group_id)`: Delete a group from Canvas synchronously

### Group Membership Management
- `push_group_memberships_sync(integration, group_id, user_ids)`: Push group memberships to Canvas synchronously
- `push_all_group_memberships_sync(integration, course_id)`: Push all group memberships for a course to Canvas synchronously

These synchronous utility functions are used in the view functions to ensure that the Canvas API operations complete fully before returning to the user, which prevents issues with the async operations being cut off prematurely when the view function returns.