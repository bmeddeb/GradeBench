"""
Setup views for Canvas integration
"""

import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import httpx

from ..models import CanvasIntegration
from ..decorators import canvas_integration_required
from ..forms import CanvasSetupForm

logger = logging.getLogger(__name__)


def get_integration_for_user(user):
    """Get or create a Canvas integration for the user"""
    try:
        integration = CanvasIntegration.objects.get(user=user)
        return integration
    except CanvasIntegration.DoesNotExist:
        return None


@login_required
def canvas_setup(request):
    """Set up Canvas API integration"""
    integration = get_integration_for_user(request.user)
    
    if request.method == "POST":
        # Use our ModelForm
        form = CanvasSetupForm(request.POST, instance=integration)
        
        if form.is_valid():
            # Create a new integration if there isn't one
            if not integration:
                integration = form.save(commit=False)
                integration.user = request.user
                integration.save()
            else:
                # Otherwise update the existing one
                form.save()
            
            messages.success(request, "Canvas integration set up successfully")
            return redirect("canvas_dashboard")
    else:
        # Initialize the form with existing integration data if available
        form = CanvasSetupForm(instance=integration)
    
    return render(request, "canvas/setup.html", {"integration": integration, "form": form})


@login_required
def canvas_list_available_courses(request):
    """
    Fetches the list of available Canvas courses for the authenticated user (preview only).
    """
    integration = get_integration_for_user(request.user)
    if not integration:
        return JsonResponse({"error": "Canvas integration not set up"}, status=400)
    
    api_url = (
        integration.canvas_url.rstrip("/")
        + "/api/v1/courses?per_page=100&enrollment_state=active"
    )
    headers = {
        "Authorization": f"Bearer {integration.api_key}",
    }
    all_courses = []
    url = api_url
    
    while url:
        resp = httpx.get(url, headers=headers)
        if resp.status_code != 200:
            return JsonResponse(
                {"error": "Failed to fetch courses from Canvas"},
                status=resp.status_code,
            )
        courses = resp.json()
        all_courses.extend(courses)
        # Handle pagination
        link = resp.headers.get("Link")
        next_url = None
        if link:
            for part in link.split(","):
                if 'rel="next"' in part:
                    next_url = part.split(";")[0].strip()[1:-1]
                    break
        url = next_url
    
    course_list = [
        {
            "id": c["id"],
            "name": c["name"],
            "course_code": c.get("course_code", ""),
            "start_at": c.get("start_at", ""),
            "end_at": c.get("end_at", ""),
            "workflow_state": c.get("workflow_state", ""),
        }
        for c in all_courses
    ]
    return JsonResponse({"courses": course_list})