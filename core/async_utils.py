"""
Async utilities for GradeBench.

This module provides utilities for working with asynchronous Django code,
particularly for wrapping synchronous Django ORM operations.
"""

import functools
import inspect
from typing import Any, Callable, TypeVar, cast

from asgiref.sync import sync_to_async

T = TypeVar("T")


def async_wrap(func: Callable[..., T]) -> Callable[..., T]:
    """
    Wraps a synchronous function to be safely called from async code.

    Args:
        func: The synchronous function to wrap

    Returns:
        An async function that wraps the synchronous function
    """

    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> T:
        return await sync_to_async(func)(*args, **kwargs)

    return wrapper


class AsyncModelMixin:
    """
    Mixin that adds async versions of common model methods.

    This mixin adds async_save, async_delete, etc. to Django models.
    """

    async def async_save(self, *args: Any, **kwargs: Any) -> None:
        """Async version of the model's save method."""
        await sync_to_async(self.save)(*args, **kwargs)

    async def async_delete(self, *args: Any, **kwargs: Any) -> None:
        """Async version of the model's delete method."""
        await sync_to_async(self.delete)(*args, **kwargs)

    @classmethod
    async def async_get(cls, *args: Any, **kwargs: Any) -> Any:
        """Async version of the model's get method."""
        return await sync_to_async(cls.objects.get)(*args, **kwargs)

    @classmethod
    async def async_filter(cls, *args: Any, **kwargs: Any) -> Any:
        """Async version of the model's filter method."""
        return await sync_to_async(cls.objects.filter)(*args, **kwargs)

    @classmethod
    async def async_all(cls) -> Any:
        """Async version of the model's all method."""
        return await sync_to_async(cls.objects.all)()

    @classmethod
    async def async_create(cls, *args: Any, **kwargs: Any) -> Any:
        """Async version of the model's create method."""
        return await sync_to_async(cls.objects.create)(*args, **kwargs)


def wrap_queryset_methods(queryset):
    """
    Dynamically wraps common QuerySet methods to be async.

    Args:
        queryset: The queryset to wrap

    Returns:
        A dict of wrapped async methods
    """
    async_methods = {}
    methods_to_wrap = [
        "get",
        "create",
        "filter",
        "all",
        "count",
        "exists",
        "first",
        "last",
        "update",
        "delete",
        "bulk_create",
    ]

    for method_name in methods_to_wrap:
        if hasattr(queryset, method_name):
            method = getattr(queryset, method_name)
            if callable(method):
                async_methods[f"async_{method_name}"] = sync_to_async(method)

    return async_methods


def wrap_manager_methods(manager):
    """
    Dynamically wraps common Manager methods to be async.

    Args:
        manager: The manager to wrap

    Returns:
        A dict of wrapped async methods
    """
    return wrap_queryset_methods(manager)
