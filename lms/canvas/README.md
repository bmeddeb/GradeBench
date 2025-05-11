# Canvas LMS Integration

This module provides integration with the Canvas Learning Management System (LMS) API, allowing GradeBench to sync course data, assignments, students, and groups.

## Architecture Overview

The integration consists of these main components:

1. **Models** (`models.py`): Django models representing Canvas entities
2. **API Client** (`client.py`): Asynchronous client for Canvas API requests
3. **Syncer** (`syncer.py`): Service to sync Canvas data with local models
4. **Sync Utilities** (`sync_utils.py`): Helper functions for common sync operations
5. **Progress Tracking** (`progress.py`): Cache-based progress tracking system
6. **Views** (`views.py`): Django views for UI and API endpoints

## Models

The main models are:

- `CanvasIntegration`: Configuration for the Canvas API connection
- `CanvasCourse`: Represents a Canvas course 
- `CanvasEnrollment`: Student or instructor enrollment in a course
- `CanvasAssignment`: Assignment in a course
- `CanvasSubmission`: Student submission for an assignment
- `CanvasGroupCategory`: Group categories/sets in a course
- `CanvasGroup`: Student groups within a category
- `CanvasGroupMembership`: Student membership in a group

## API Client

The `Client` class in `client.py` provides an asynchronous interface to the Canvas API using `httpx`. It handles:

- Authentication with API token
- Pagination of API responses
- Rate limiting and error handling
- Methods for each API endpoint (courses, assignments, groups, etc.)

## Syncing Process

To sync data from Canvas:

1. Initialize a `Client` with a `CanvasIntegration` instance
2. Call `sync_course()` or `sync_all_courses()` to fetch data
3. Data is saved to local database models
4. Group data is synced to the core `Team` model
5. Group memberships are synced to `Student` team assignments

## Asynchronous Operation

Most operations use Django's asynchronous features:

- API requests are made asynchronously with `httpx`
- Database operations use Django's async ORM methods (aget, aupdate_or_create, etc.)
- The `AsyncModelMixin` adds async capabilities to models
- `sync_to_async` is used to call synchronous code from async context
- Background sync operations run in separate threads using `run_async_in_thread`

## Progress Tracking

Long-running operations use a cache-based progress tracking system:

1. `SyncProgress` initializes a progress record in the cache
2. During processing, the progress is updated with current status
3. The UI can fetch progress updates via a polling API endpoint
4. On completion, final status and results are saved

## Common Utilities

The `SafeAsyncAccessor` class provides a safe way to access model attributes and relationships in asynchronous contexts without violating Django's synchronous-only database operations rule.

## Error Handling

Errors are handled at multiple levels:

1. Individual entity processing errors are logged but don't stop the overall sync
2. Sync operations for course/group/student continue even if specific entities fail
3. Progress tracking includes error details for UI feedback
4. Background thread operations catch and log errors to prevent crashes

## UI Integration

The Canvas integration provides:

1. Setup page for API configuration
2. Dashboard for courses overview
3. Course detail pages showing assignments, students, and groups
4. Sync progress tracking with visual feedback
5. API endpoints for course selection and sync operations