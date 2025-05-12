"""
Decorators for Canvas-related views
"""

import functools
from django.shortcuts import redirect
from django.http import JsonResponse
from django.contrib import messages

from .models import CanvasIntegration


def canvas_integration_required(view_func):
    """
    Decorator that checks if user has a Canvas integration set up.
    Attaches the integration to request.canvas_integration if found.
    
    Redirects to canvas_setup if integration not found.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")
        
        try:
            integration = CanvasIntegration.objects.get(user=request.user)
            # Attach integration to request
            request.canvas_integration = integration
            return view_func(request, *args, **kwargs)
        except CanvasIntegration.DoesNotExist:
            return redirect("canvas_setup")
    
    return wrapper


def canvas_integration_required_json(view_func):
    """
    Decorator that checks if user has a Canvas integration set up.
    Returns JSON response for AJAX views instead of redirecting.
    
    Attaches the integration to request.canvas_integration if found.
    """
    @functools.wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({"success": False, "error": "Authentication required"}, status=401)
        
        try:
            integration = CanvasIntegration.objects.get(user=request.user)
            # Attach integration to request
            request.canvas_integration = integration
            return view_func(request, *args, **kwargs)
        except CanvasIntegration.DoesNotExist:
            return JsonResponse({"success": False, "error": "Canvas integration not set up"}, status=403)
    
    return wrapper