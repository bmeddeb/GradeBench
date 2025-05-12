# lms/canvas/progress.py

import uuid
from django.core.cache import cache
from django.utils import timezone
from asgiref.sync import sync_to_async


class SyncProgress:
    """
    Helper class to track sync progress for courses and assignments.
    Uses Django's cache to store progress information.
    """

    STATUS_PENDING = "pending"
    STATUS_FETCHING_COURSE = "fetching_course"
    STATUS_FETCHING_ENROLLMENTS = "fetching_enrollments"
    STATUS_FETCHING_USERS = "fetching_users"
    STATUS_FETCHING_ASSIGNMENTS = "fetching_assignments"
    STATUS_FETCHING_SUBMISSIONS = "fetching_submissions"
    STATUS_PROCESSING_SUBMISSIONS = "processing_submissions"
    STATUS_SAVING_DATA = "saving_data"
    STATUS_COMPLETED = "completed"
    STATUS_ERROR = "error"

    STATUS_QUEUED = "queued"
    STATUS_IN_PROGRESS = "in_progress"
    STATUS_SUCCESS = "success"

    @staticmethod
    def get_cache_key(user_id, course_id=None):
        """Get the cache key for a user's sync progress."""
        if course_id:
            return f"sync_progress_{user_id}_{course_id}"
        return f"sync_progress_{user_id}"

    @staticmethod
    def get_batch_cache_key(user_id, batch_id):
        """Get the cache key for a batch sync operation."""
        return f"sync_batch_{user_id}_{batch_id}"

    @staticmethod
    def update(
        user_id,
        course_id=None,
        current=0,
        total=0,
        status=STATUS_PENDING,
        message=None,
        error=None,
    ):
        """Update the sync progress for a user."""
        cache_key = SyncProgress.get_cache_key(user_id, course_id)
        progress_data = {
            "course_id": course_id,
            "current": current,
            "total": total,
            "status": status,
            "message": message,
            "error": error,
            "updated_at": timezone.now().isoformat(),
        }
        cache.set(cache_key, progress_data, timeout=3600)  # 1 hour timeout
        return progress_data

    @staticmethod
    def update_batch(
        user_id,
        batch_id,
        course_statuses,
        current=0,
        total=0,
        status=STATUS_IN_PROGRESS,
        message=None,
        error=None,
    ):
        """Update progress for a batch of courses."""
        cache_key = SyncProgress.get_batch_cache_key(user_id, batch_id)
        progress_data = {
            "batch_id": batch_id,
            "current": current,
            "total": total,
            "status": status,
            "message": message,
            "error": error,
            "course_statuses": course_statuses,  # Dict with course_id as key
            "updated_at": timezone.now().isoformat(),
        }
        cache.set(cache_key, progress_data, timeout=3600)  # 1 hour timeout
        return progress_data

    @staticmethod
    def get(user_id, course_id=None):
        """Get the sync progress for a user."""
        cache_key = SyncProgress.get_cache_key(user_id, course_id)
        progress = cache.get(cache_key, {})
        return progress

    @staticmethod
    def get_batch_progress(user_id, batch_id):
        """Get batch progress data."""
        cache_key = SyncProgress.get_batch_cache_key(user_id, batch_id)
        return cache.get(cache_key, {})

    @staticmethod
    def clear(user_id, course_id=None):
        """Clear the sync progress for a user."""
        cache_key = SyncProgress.get_cache_key(user_id, course_id)
        cache.delete(cache_key)

    @staticmethod
    def clear_batch(user_id, batch_id):
        """Clear the batch progress for a user."""
        cache_key = SyncProgress.get_batch_cache_key(user_id, batch_id)
        cache.delete(cache_key)

    @staticmethod
    def start_sync(user_id, course_id=None, total_steps=4):
        """Start tracking a new sync operation."""
        return SyncProgress.update(
            user_id,
            course_id,
            current=0,
            total=total_steps,
            status=SyncProgress.STATUS_PENDING,
            message="Initializing sync...",
        )

    @staticmethod
    def start_batch_sync(user_id, course_ids, course_names=None):
        """
        Start tracking a batch sync operation.
        
        Args:
            user_id: The user ID initiating the sync
            course_ids: List of course IDs to sync
            course_names: Optional dict mapping course_ids to their names
        
        Returns:
            dict: Batch ID and initial progress data
        """
        batch_id = str(uuid.uuid4())
        
        # Initialize course statuses
        course_statuses = {}
        for course_id in course_ids:
            course_str_id = str(course_id)
            course_statuses[course_str_id] = {
                "name": course_names.get(course_str_id, f"Course {course_id}") if course_names else f"Course {course_id}",
                "status": SyncProgress.STATUS_QUEUED,
                "progress": 0,
                "message": "Waiting to start",
                "started_at": None,
                "completed_at": None
            }
        
        # Create initial batch progress
        SyncProgress.update_batch(
            user_id,
            batch_id,
            course_statuses,
            current=0,
            total=len(course_ids),
            status=SyncProgress.STATUS_PENDING,
            message="Preparing to sync courses..."
        )
        
        return {
            "batch_id": batch_id,
            "progress": SyncProgress.get_batch_progress(user_id, batch_id)
        }

    @staticmethod
    def complete_sync(user_id, course_id=None, success=True, message=None, error=None):
        """Mark a sync operation as completed."""
        progress = SyncProgress.get(user_id, course_id)
        total = progress.get("total", 1)

        if success:
            return SyncProgress.update(
                user_id,
                course_id,
                current=total,
                total=total,
                status=SyncProgress.STATUS_COMPLETED,
                message=message or "Sync completed successfully.",
            )
        else:
            return SyncProgress.update(
                user_id,
                course_id,
                current=progress.get("current", 0),
                total=total,
                status=SyncProgress.STATUS_ERROR,
                message=message or "Sync failed.",
                error=error,
            )

    @staticmethod
    def complete_batch_sync(user_id, batch_id, success=True, message=None, error=None):
        """Mark a batch sync operation as completed."""
        progress = SyncProgress.get_batch_progress(user_id, batch_id)
        total = progress.get("total", 1)
        course_statuses = progress.get("course_statuses", {})

        status = SyncProgress.STATUS_COMPLETED if success else SyncProgress.STATUS_ERROR
        
        return SyncProgress.update_batch(
            user_id,
            batch_id,
            course_statuses,
            current=total,
            total=total,
            status=status,
            message=message or ("Batch sync completed successfully." if success else "Batch sync failed."),
            error=error
        )

    # Async versions of the methods for use in async views/client code

    @staticmethod
    async def async_update(
        user_id,
        course_id=None,
        current=0,
        total=0,
        status=STATUS_PENDING,
        message=None,
        error=None,
    ):
        """Async version of update method."""
        return await sync_to_async(SyncProgress.update)(
            user_id, course_id, current, total, status, message, error
        )

    @staticmethod
    async def async_update_batch(
        user_id,
        batch_id,
        course_statuses,
        current=0,
        total=0,
        status=STATUS_IN_PROGRESS,
        message=None,
        error=None,
    ):
        """Async version of update_batch method."""
        return await sync_to_async(SyncProgress.update_batch)(
            user_id, batch_id, course_statuses, current, total, status, message, error
        )

    @staticmethod
    async def async_get(user_id, course_id=None):
        """Async version of get method."""
        return await sync_to_async(SyncProgress.get)(user_id, course_id)

    @staticmethod
    async def async_get_batch_progress(user_id, batch_id):
        """Async version of get_batch_progress method."""
        return await sync_to_async(SyncProgress.get_batch_progress)(user_id, batch_id)

    @staticmethod
    async def async_clear(user_id, course_id=None):
        """Async version of clear method."""
        return await sync_to_async(SyncProgress.clear)(user_id, course_id)

    @staticmethod
    async def async_clear_batch(user_id, batch_id):
        """Async version of clear_batch method."""
        return await sync_to_async(SyncProgress.clear_batch)(user_id, batch_id)

    @staticmethod
    async def async_start_sync(user_id, course_id=None, total_steps=4):
        """Async version of start_sync method."""
        return await sync_to_async(SyncProgress.start_sync)(
            user_id, course_id, total_steps
        )

    @staticmethod
    async def async_start_batch_sync(user_id, course_ids, course_names=None):
        """Async version of start_batch_sync method."""
        return await sync_to_async(SyncProgress.start_batch_sync)(
            user_id, course_ids, course_names
        )

    @staticmethod
    async def async_complete_sync(
        user_id, course_id=None, success=True, message=None, error=None
    ):
        """Async version of complete_sync method."""
        return await sync_to_async(SyncProgress.complete_sync)(
            user_id, course_id, success, message, error
        )

    @staticmethod
    async def async_complete_batch_sync(
        user_id, batch_id, success=True, message=None, error=None
    ):
        """Async version of complete_batch_sync method."""
        return await sync_to_async(SyncProgress.complete_batch_sync)(
            user_id, batch_id, success, message, error
        )
