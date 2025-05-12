"""
Async helpers for authentication backends.

This module contains functions to make social authentication backends
compatible with Django's async views.
"""

from django.contrib.auth import get_backends
from django.contrib.auth.models import AnonymousUser
from django.http import HttpResponseRedirect
from asgiref.sync import sync_to_async
import inspect
import functools
from typing import Any, Optional, Type, Dict, List, Callable
import logging

logger = logging.getLogger(__name__)

class AsyncCompatSocialAuthBackendMixin:
    """
    A mixin that adds async versions of auth methods to authentication backends.
    """

    async def aget_user(self, user_id: int) -> Any:
        """
        Async version of get_user method.
        Wraps the synchronous get_user method to be used in async context.
        """
        return await sync_to_async(self.get_user)(user_id)

    async def aauthenticate(self, request: Any, **credentials) -> Any:
        """
        Async version of authenticate method.
        Wraps the synchronous authenticate method to be used in async context.
        """
        return await sync_to_async(self.authenticate)(request, **credentials)


def wrap_auth_backend(backend: Any) -> Any:
    """
    Wraps an authentication backend with async-compatible methods.

    Args:
        backend: The authentication backend to wrap

    Returns:
        The same backend instance, now with async methods
    """
    # Check if backend already has async methods
    if hasattr(backend, 'aget_user') and inspect.iscoroutinefunction(backend.aget_user):
        # Backend already has async methods, no need to wrap
        return backend

    # Create a new subclass of the backend class with the async mixin
    backend_class = backend.__class__
    async_backend_class = type(
        f"Async{backend_class.__name__}",
        (AsyncCompatSocialAuthBackendMixin, backend_class),
        {}
    )

    # Create a new instance of the async backend class with the same attributes
    async_backend = async_backend_class()
    for attr_name in dir(backend):
        if attr_name.startswith('__'):
            continue
        try:
            setattr(async_backend, attr_name, getattr(backend, attr_name))
        except (AttributeError, TypeError):
            pass

    return async_backend


def patch_auth_backends() -> None:
    """
    Patch all authentication backends to be async-compatible.
    This function should be called at Django startup.
    """
    backends = get_backends()
    for i, backend in enumerate(backends):
        if not hasattr(backend, 'aget_user') or not inspect.iscoroutinefunction(backend.aget_user):
            backends[i] = wrap_auth_backend(backend)

    # Monkeypatch Django's login_required decorator to work with async views
    # This is done by looking for the original decorator in the module namespace
    try:
        from django.contrib.auth.decorators import login_required as original_login_required
        import django.contrib.auth.decorators

        # Store the original decorator for use in our implementation
        original_sync_login_required = original_login_required

        # Define our async-compatible login_required decorator
        def async_login_required(function=None, redirect_field_name=None, login_url=None):
            """
            Async-compatible version of the login_required decorator.
            """
            def decorator(view_func):
                # Check if the view is async
                if inspect.iscoroutinefunction(view_func):
                    @functools.wraps(view_func)
                    async def wrapper(request, *args, **kwargs):
                        if not request.user.is_authenticated:
                            from django.conf import settings
                            resolved_login_url = login_url or settings.LOGIN_URL
                            return HttpResponseRedirect(resolved_login_url)
                        return await view_func(request, *args, **kwargs)
                    return wrapper
                else:
                    # Use the original decorator for synchronous views
                    return original_sync_login_required(
                        function=view_func,
                        redirect_field_name=redirect_field_name,
                        login_url=login_url
                    )

            if function:
                return decorator(function)
            return decorator

        # Replace the original decorator with our async-compatible version
        django.contrib.auth.decorators.login_required = async_login_required
        logger.info("Successfully patched Django's login_required decorator for async compatibility")
    except (ImportError, AttributeError) as e:
        logger.warning(f"Could not patch Django's login_required decorator: {e}")
        # Continue without patching - the standard decorator will continue to work for sync views