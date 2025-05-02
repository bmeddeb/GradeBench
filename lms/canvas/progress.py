# lms/canvas/progress.py

from django.core.cache import cache
from django.utils import timezone
from asgiref.sync import sync_to_async

class SyncProgress:
    """
    Helper class to track sync progress for courses and assignments.
    Uses Django's cache to store progress information.
    """
    
    STATUS_PENDING = 'pending'
    STATUS_FETCHING_COURSE = 'fetching_course'
    STATUS_FETCHING_ENROLLMENTS = 'fetching_enrollments'
    STATUS_FETCHING_USERS = 'fetching_users'
    STATUS_FETCHING_ASSIGNMENTS = 'fetching_assignments'
    STATUS_FETCHING_SUBMISSIONS = 'fetching_submissions'
    STATUS_PROCESSING_SUBMISSIONS = 'processing_submissions'
    STATUS_SAVING_DATA = 'saving_data'
    STATUS_COMPLETED = 'completed'
    STATUS_ERROR = 'error'
    
    @staticmethod
    def get_cache_key(user_id, course_id=None):
        """Get the cache key for a user's sync progress."""
        if course_id:
            return f"sync_progress_{user_id}_{course_id}"
        return f"sync_progress_{user_id}"
    
    @staticmethod
    def update(user_id, course_id=None, current=0, total=0, status=STATUS_PENDING, message=None, error=None):
        """Update the sync progress for a user."""
        cache_key = SyncProgress.get_cache_key(user_id, course_id)
        progress_data = {
            "course_id": course_id,
            "current": current,
            "total": total,
            "status": status,
            "message": message,
            "error": error,
            "updated_at": timezone.now().isoformat()
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
    def clear(user_id, course_id=None):
        """Clear the sync progress for a user."""
        cache_key = SyncProgress.get_cache_key(user_id, course_id)
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
            message="Initializing sync..."
        )
    
    @staticmethod
    def complete_sync(user_id, course_id=None, success=True, message=None, error=None):
        """Mark a sync operation as completed."""
        progress = SyncProgress.get(user_id, course_id)
        total = progress.get('total', 1)
        
        if success:
            return SyncProgress.update(
                user_id, 
                course_id, 
                current=total, 
                total=total, 
                status=SyncProgress.STATUS_COMPLETED,
                message=message or "Sync completed successfully."
            )
        else:
            return SyncProgress.update(
                user_id, 
                course_id, 
                current=progress.get('current', 0), 
                total=total, 
                status=SyncProgress.STATUS_ERROR,
                message=message or "Sync failed.",
                error=error
            )
    
    # Async versions of the methods for use in async views/client code
    
    @staticmethod
    async def async_update(user_id, course_id=None, current=0, total=0, status=STATUS_PENDING, message=None, error=None):
        """Async version of update method."""
        return await sync_to_async(SyncProgress.update)(
            user_id, course_id, current, total, status, message, error
        )
    
    @staticmethod
    async def async_get(user_id, course_id=None):
        """Async version of get method."""
        return await sync_to_async(SyncProgress.get)(user_id, course_id)
    
    @staticmethod
    async def async_clear(user_id, course_id=None):
        """Async version of clear method."""
        return await sync_to_async(SyncProgress.clear)(user_id, course_id)
    
    @staticmethod
    async def async_start_sync(user_id, course_id=None, total_steps=4):
        """Async version of start_sync method."""
        return await sync_to_async(SyncProgress.start_sync)(user_id, course_id, total_steps)
    
    @staticmethod
    async def async_complete_sync(user_id, course_id=None, success=True, message=None, error=None):
        """Async version of complete_sync method."""
        return await sync_to_async(SyncProgress.complete_sync)(user_id, course_id, success, message, error)