# lms/utils.py
"""
Common utility functions for the LMS app.
"""

import logging
import threading
import asyncio
from typing import Optional, Any, Callable, Awaitable, TypeVar
from django.contrib.auth.models import User
from django.http import HttpRequest
from asgiref.sync import sync_to_async

from lms.canvas.models import CanvasIntegration
from lms.canvas.progress import SyncProgress

logger = logging.getLogger(__name__)

# Type variables for generics
T = TypeVar("T")
R = TypeVar("R")


def get_integration_for_user(user: User) -> Optional[CanvasIntegration]:
    """
    Get the Canvas integration for a user.

    Args:
        user: The user to get the integration for

    Returns:
        The CanvasIntegration for the user, or None if it doesn't exist
    """
    try:
        return CanvasIntegration.objects.get(user=user)
    except CanvasIntegration.DoesNotExist:
        return None


async def aget_integration_for_user(user: User) -> Optional[CanvasIntegration]:
    """
    Async version of get_integration_for_user.

    Args:
        user: The user to get the integration for

    Returns:
        The CanvasIntegration for the user, or None if it doesn't exist
    """
    return await sync_to_async(get_integration_for_user)(user)


def run_async_in_thread(
    async_func: Callable[..., Awaitable[T]], *args, **kwargs
) -> threading.Thread:
    """
    Run an async function in a separate thread.

    Args:
        async_func: The async function to run
        *args: Positional arguments to pass to the function
        **kwargs: Keyword arguments to pass to the function

    Returns:
        The thread that was started
    """

    def run():
        try:
            asyncio.run(async_func(*args, **kwargs))
        except Exception as e:
            logger.error(f"Error in async thread: {e}")
            # If user_id is provided, update progress with error
            user_id = kwargs.get("user_id")
            course_id = kwargs.get("course_id")
            if user_id:
                SyncProgress.complete_sync(
                    user_id,
                    course_id,
                    success=False,
                    message="Operation failed with an error",
                    error=str(e),
                )

    thread = threading.Thread(target=run)
    thread.daemon = True
    thread.start()
    return thread


def handle_sync_progress(request: HttpRequest, course_id: Optional[int] = None) -> None:
    """
    Update session to indicate a sync is in progress.

    Args:
        request: The current request
        course_id: Optional course ID if syncing a specific course
    """
    if course_id:
        request.session[f"canvas_sync_course_{course_id}_in_progress"] = True
    else:
        request.session["canvas_sync_in_progress"] = True
        request.session["canvas_sync_started"] = True


class SafeAsyncAccessor:
    """Helper class for safely accessing attributes in async context."""

    @staticmethod
    async def get_attr(obj: Any, attr: str) -> Any:
        """
        Safely get an attribute from an object in async context.

        Args:
            obj: The object to get the attribute from
            attr: The name of the attribute to get

        Returns:
            The attribute value
        """
        return await sync_to_async(lambda: getattr(obj, attr, None))()

    @staticmethod
    async def call_method(obj: Any, method: str, *args, **kwargs) -> Any:
        """
        Safely call a method on an object in async context.

        Args:
            obj: The object to call the method on
            method: The name of the method to call
            *args: Positional arguments to pass to the method
            **kwargs: Keyword arguments to pass to the method

        Returns:
            The result of the method call
        """
        method_func = getattr(obj, method, None)
        if not method_func or not callable(method_func):
            return None
        return await sync_to_async(lambda: method_func(*args, **kwargs))()
