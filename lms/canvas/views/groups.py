"""
Views for Canvas groups management
"""

import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Count, Q

from ..models import (
    CanvasCourse,
    CanvasEnrollment,
    CanvasGroupCategory,
    CanvasGroup,
    CanvasGroupMembership,
)
from ..decorators import canvas_integration_required, canvas_integration_required_json
from ..utils import get_json_error_response, get_json_success_response
from ..sync_utils import (
    create_group_category_sync,
    update_group_category_sync,
    delete_group_category_sync,
    create_group_sync,
    update_group_sync,
    delete_group_sync,
    push_all_group_memberships_sync,
)

logger = logging.getLogger(__name__)


@method_decorator(canvas_integration_required, name='dispatch')
class CourseGroupsView(ListView):
    """View for course groups by category"""
    template_name = "canvas/groups/index.html"
    context_object_name = "category_data"
    
    def get_queryset(self):
        """Get group categories with counts"""
        integration = self.request.canvas_integration
        course_id = self.kwargs.get('course_id')
        
        course = get_object_or_404(
            CanvasCourse, 
            canvas_id=course_id, 
            integration=integration
        )
        
        # Store course on instance for get_context_data
        self.course = course
        
        # Get all group categories for this course
        categories = CanvasGroupCategory.objects.filter(
            course=course
        ).order_by("name")
        
        # For each category, get group and member counts
        category_data = []
        for category in categories:
            groups_count = CanvasGroup.objects.filter(category=category).count()
            
            # Count members across all groups in this category
            memberships_count = CanvasGroupMembership.objects.filter(
                group__category=category
            ).count()
            
            category_data.append({
                "category": category,
                "groups_count": groups_count,
                "members_count": memberships_count,
            })
        
        return category_data
    
    def get_context_data(self, **kwargs):
        """Add course and student count data"""
        context = super().get_context_data(**kwargs)
        course = self.course
        
        # Get total number of students and unassigned count
        total_students = CanvasEnrollment.objects.filter(
            course=course, role="StudentEnrollment"
        ).count()
        
        # Find students who have group memberships
        students_with_groups = CanvasGroupMembership.objects.filter(
            group__category__course=course
        ).values_list("user_id", flat=True).distinct()
        
        # Count students without group memberships
        unassigned_students = CanvasEnrollment.objects.filter(
            course=course,
            role="StudentEnrollment"
        ).exclude(
            user_id__in=students_with_groups
        ).count()
        
        # Pass first category as default selected if exists
        default_category = None
        if self.object_list:
            default_category = self.object_list[0]["category"]
        
        # Sync status info
        last_sync = course.updated_at if hasattr(course, "updated_at") else None
        
        context.update({
            "course": course,
            "total_students": total_students,
            "unassigned_students": unassigned_students,
            "last_sync": last_sync,
            "default_category": default_category,
        })
        
        return context


@canvas_integration_required_json
def group_set_detail(request, course_id, group_set_id):
    """
    AJAX endpoint to get detailed info about a specific group set,
    including all groups and their members
    """
    integration = request.canvas_integration
    
    course = get_object_or_404(
        CanvasCourse, canvas_id=course_id, integration=integration)
    
    # Get the group category (set)
    try:
        category = get_object_or_404(
            CanvasGroupCategory, id=group_set_id, course=course)
    except CanvasGroupCategory.DoesNotExist:
        return JsonResponse(
            get_json_error_response("Group set not found"),
            status=404
        )
    
    # Get all groups in this category
    groups = CanvasGroup.objects.filter(category=category).order_by("name")
    
    # Build response with groups and their members
    group_data = []
    for group in groups:
        # Get members for this group
        memberships = CanvasGroupMembership.objects.filter(group=group)
        
        # Get the associated core team if it exists
        core_team = None
        if hasattr(group, "core_team") and group.core_team:
            core_team = {
                "id": group.core_team.id,
                "name": group.core_team.name,
            }
        
        # Add to response
        group_data.append({
            "id": group.id,
            "canvas_id": group.canvas_id,
            "name": group.name,
            "description": group.description,
            "created_at": group.created_at.isoformat() if group.created_at else None,
            "members": [
                {
                    "id": membership.id,
                    "user_id": membership.user_id,
                    "name": membership.name,
                    "email": membership.email,
                    "student_id": membership.student_id if hasattr(membership, "student") else None,
                }
                for membership in memberships
            ],
            "core_team": core_team,
        })
    
    # Get unassigned students
    assigned_student_ids = CanvasGroupMembership.objects.filter(
        group__category=category
    ).values_list("user_id", flat=True)
    
    unassigned_students = CanvasEnrollment.objects.filter(
        course=course,
        role="StudentEnrollment"
    ).exclude(
        user_id__in=assigned_student_ids
    ).values("user_id", "user_name", "email")
    
    # Build response
    response_data = {
        "category": {
            "id": category.id,
            "canvas_id": category.canvas_id,
            "name": category.name,
            "self_signup": category.self_signup,
            "group_limit": category.group_limit,
            "auto_leader": category.auto_leader,
            "created_at": category.created_at.isoformat() if category.created_at else None,
        },
        "groups": group_data,
        "unassigned_students": list(unassigned_students),
    }
    
    return JsonResponse(response_data)


@canvas_integration_required
def create_group_set(request, course_id):
    """
    Create a new group set (category) for a course.
    This creates both in the local database and in Canvas.
    """
    integration = request.canvas_integration
    
    # Get the course
    course = get_object_or_404(
        CanvasCourse, canvas_id=course_id, integration=integration
    )
    
    if request.method == "POST":
        # Create the group set in Canvas and locally
        name = request.POST.get("name")
        self_signup = request.POST.get("self_signup")
        auto_leader = request.POST.get("auto_leader")
        group_limit = request.POST.get("group_limit")
        
        if not name:
            messages.error(request, "Group set name is required")
            return render(request, "canvas/groups/create_group_set.html", {
                "course": course,
            })
        
        # Convert empty string to None for numeric field
        if group_limit == "":
            group_limit = None
        
        try:
            category, created = create_group_category_sync(
                integration=integration,
                course_id=course_id,
                name=name,
                self_signup=self_signup,
                auto_leader=auto_leader,
                group_limit=group_limit
            )
            
            messages.success(
                request, f"Group set '{name}' created successfully")
            return redirect("canvas_course_groups", course_id=course_id)
        
        except Exception as e:
            messages.error(request, f"Error creating group set: {str(e)}")
            return render(request, "canvas/groups/create_group_set.html", {
                "course": course,
                "error": str(e),
            })
    
    # GET request - show the form
    return render(request, "canvas/groups/create_group_set.html", {
        "course": course,
    })


@canvas_integration_required
def edit_group_set(request, course_id, group_set_id):
    """
    Edit a group set (category).
    This updates both the local database and Canvas.
    """
    integration = request.canvas_integration
    
    # Get the course and group set
    course = get_object_or_404(
        CanvasCourse, canvas_id=course_id, integration=integration)
    group_set = get_object_or_404(
        CanvasGroupCategory, id=group_set_id, course=course)
    
    if request.method == "POST":
        # Update the group set in Canvas and locally
        name = request.POST.get("name")
        self_signup = request.POST.get("self_signup")
        auto_leader = request.POST.get("auto_leader")
        group_limit = request.POST.get("group_limit")
        
        if not name:
            messages.error(request, "Group set name is required")
            return render(request, "canvas/groups/edit_group_set.html", {
                "course": course,
                "group_set": group_set,
            })
        
        # Convert empty string to None for numeric field
        if group_limit == "":
            group_limit = None
        
        try:
            category, updated = update_group_category_sync(
                integration=integration,
                category_id=group_set.canvas_id,
                name=name,
                self_signup=self_signup,
                auto_leader=auto_leader,
                group_limit=group_limit
            )
            
            messages.success(
                request, f"Group set '{name}' updated successfully")
            return redirect("canvas_course_groups", course_id=course_id)
        
        except Exception as e:
            messages.error(request, f"Error updating group set: {str(e)}")
            return render(request, "canvas/groups/edit_group_set.html", {
                "course": course,
                "group_set": group_set,
                "error": str(e),
            })
    
    # GET request - show the form
    return render(request, "canvas/groups/edit_group_set.html", {
        "course": course,
        "group_set": group_set,
    })


@require_POST
@canvas_integration_required_json
def delete_group_set(request, course_id, group_set_id):
    """
    Delete a group set (category).
    This deletes from both the local database and Canvas.
    """
    integration = request.canvas_integration
    
    # Get the course and group set
    course = get_object_or_404(
        CanvasCourse, canvas_id=course_id, integration=integration)
    group_set = get_object_or_404(
        CanvasGroupCategory, id=group_set_id, course=course)
    
    try:
        # Store the name before deletion
        group_set_name = group_set.name
        canvas_category_id = group_set.canvas_id
        
        # Delete the group category
        success = delete_group_category_sync(
            integration=integration,
            category_id=canvas_category_id
        )
        
        return JsonResponse(get_json_success_response(
            f"Group set '{group_set_name}' deleted successfully"
        ))
    
    except Exception as e:
        return JsonResponse(
            get_json_error_response(f"Error deleting group set: {str(e)}"),
            status=500
        )


@canvas_integration_required
def create_group(request, course_id, group_set_id):
    """
    Create a new group within a group set.
    This creates both in the local database and in Canvas.
    """
    integration = request.canvas_integration
    
    # Get the course and group set
    course = get_object_or_404(
        CanvasCourse, canvas_id=course_id, integration=integration)
    group_set = get_object_or_404(
        CanvasGroupCategory, id=group_set_id, course=course)
    
    if request.method == "POST":
        # Create the group in Canvas and locally
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        
        if not name:
            messages.error(request, "Group name is required")
            return render(request, "canvas/groups/create_group.html", {
                "course": course,
                "group_set": group_set,
            })
        
        try:
            group, created = create_group_sync(
                integration=integration,
                category_id=group_set.canvas_id,
                name=name,
                description=description
            )
            
            messages.success(request, f"Group '{name}' created successfully")
            return redirect("canvas_course_groups", course_id=course_id)
        
        except Exception as e:
            messages.error(request, f"Error creating group: {str(e)}")
            return render(request, "canvas/groups/create_group.html", {
                "course": course,
                "group_set": group_set,
                "error": str(e),
            })
    
    # GET request - show the form
    return render(request, "canvas/groups/create_group.html", {
        "course": course,
        "group_set": group_set,
    })


@canvas_integration_required
def edit_group(request, course_id, group_id):
    """
    Edit a group.
    This updates both the local database and Canvas.
    """
    integration = request.canvas_integration
    
    # Get the course and group
    course = get_object_or_404(
        CanvasCourse, canvas_id=course_id, integration=integration)
    group = get_object_or_404(CanvasGroup, id=group_id)
    
    # Verify the group belongs to this course
    if group.category.course != course:
        messages.error(request, "Group does not belong to this course")
        return redirect("canvas_course_groups", course_id=course_id)
    
    if request.method == "POST":
        # Update the group in Canvas and locally
        name = request.POST.get("name")
        description = request.POST.get("description", "")
        
        if not name:
            messages.error(request, "Group name is required")
            return render(request, "canvas/groups/edit_group.html", {
                "course": course,
                "group": group,
            })
        
        try:
            updated_group, updated = update_group_sync(
                integration=integration,
                group_id=group.canvas_id,
                name=name,
                description=description
            )
            
            messages.success(request, f"Group '{name}' updated successfully")
            return redirect("canvas_course_groups", course_id=course_id)
        
        except Exception as e:
            messages.error(request, f"Error updating group: {str(e)}")
            return render(request, "canvas/groups/edit_group.html", {
                "course": course,
                "group": group,
                "error": str(e),
            })
    
    # GET request - show the form
    return render(request, "canvas/groups/edit_group.html", {
        "course": course,
        "group": group,
    })


@require_POST
@canvas_integration_required_json
def delete_group(request, course_id, group_id):
    """
    Delete a group.
    This deletes from both the local database and Canvas.
    """
    integration = request.canvas_integration
    
    # Get the course and group
    course = get_object_or_404(
        CanvasCourse, canvas_id=course_id, integration=integration)
    group = get_object_or_404(CanvasGroup, id=group_id)
    
    # Verify the group belongs to this course
    if group.category.course != course:
        return JsonResponse(
            get_json_error_response("Group does not belong to this course"),
            status=403
        )
    
    try:
        # Store the name before deletion
        group_name = group.name
        canvas_group_id = group.canvas_id
        
        # Delete the group
        success = delete_group_sync(
            integration=integration,
            group_id=canvas_group_id
        )
        
        return JsonResponse(get_json_success_response(
            f"Group '{group_name}' deleted successfully"
        ))
    
    except Exception as e:
        return JsonResponse(
            get_json_error_response(f"Error deleting group: {str(e)}"),
            status=500
        )


@canvas_integration_required
def push_course_group_memberships(request, course_id):
    """
    Explicitly push all group memberships for a course to Canvas.
    This ensures Canvas has the same group memberships as our local database.
    """
    integration = request.canvas_integration
    
    # Get the course
    course = get_object_or_404(
        CanvasCourse, canvas_id=course_id, integration=integration
    )
    
    if request.method == "POST":
        try:
            # Push all memberships
            stats = push_all_group_memberships_sync(integration, course_id)
            
            if stats["errors"] > 0:
                messages.warning(
                    request,
                    f"Pushed memberships for {stats['groups_updated']} groups, but encountered {stats['errors']} errors. See logs for details."
                )
            else:
                messages.success(
                    request,
                    f"Successfully pushed memberships for {stats['groups_updated']} groups to Canvas."
                )
            
            return redirect("canvas_course_groups", course_id=course_id)
        
        except Exception as e:
            messages.error(
                request, f"Error pushing group memberships: {str(e)}")
            return redirect("canvas_course_groups", course_id=course_id)
    
    # If it's a GET request, show confirmation page
    return render(
        request,
        "canvas/groups/confirm_push_memberships.html",
        {
            "course": course,
        },
    )


# Function-based views for compatibility
course_groups = CourseGroupsView.as_view()