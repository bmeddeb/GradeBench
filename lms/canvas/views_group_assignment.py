"""
Phase 3: Canvas group student assignment views for SortableJS implementation
These view functions support the drag-and-drop functionality for assigning students to groups.
"""

import json
import logging
import random
from typing import Dict, Any, List, Optional

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

from lms.canvas.models import (
    CanvasCourse,
    CanvasEnrollment,
    CanvasGroup,
    CanvasGroupCategory,
    CanvasGroupMembership,
)
from core.models import Student, Team
from .views import get_integration_for_user
from .sync_utils import push_team_assignments_to_canvas

logger = logging.getLogger(__name__)


@login_required
@require_POST
def add_student_to_group(request, course_id, group_id):
    """
    Add a student to a Canvas group via AJAX.
    This supports individual drag-and-drop assignments.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Authentication required"}, status=401)

    try:
        # Parse request data
        data = json.loads(request.body)
        student_id = data.get("student_id")
        
        if not student_id:
            return JsonResponse({"success": False, "error": "Student ID is required"}, status=400)
            
        # Get the necessary objects
        integration = get_integration_for_user(request.user)
        if not integration:
            return JsonResponse({"success": False, "error": "Canvas integration not set up"}, status=403)
        
        course = get_object_or_404(CanvasCourse, canvas_id=course_id, integration=integration)
        group = get_object_or_404(CanvasGroup, id=group_id)
        
        if group.category.course != course:
            return JsonResponse({"success": False, "error": "Group does not belong to this course"}, status=403)
        
        # Find the student enrollment
        enrollment = get_object_or_404(CanvasEnrollment, course=course, user_id=student_id)
        
        # Get or create student record
        student = enrollment.student
        if not student:
            # Parse user name
            user_name_parts = enrollment.user_name.split()
            first_name = user_name_parts[0] if user_name_parts else "Unknown"
            last_name = " ".join(user_name_parts[1:]) if len(user_name_parts) > 1 else ""
            
            # Create the student record
            student, created = Student.objects.update_or_create(
                canvas_user_id=student_id,
                defaults={
                    "email": enrollment.email or f"canvas-user-{student_id}@example.com",
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )
            
            # Link student to enrollment
            enrollment.student = student
            enrollment.save(update_fields=["student"])
        
        # Get or create team link
        team = group.core_team
        if not team:
            team, created = Team.objects.update_or_create(
                canvas_group_id=group.canvas_id,
                canvas_course=course,
                defaults={
                    "name": group.name[:100],
                    "description": group.description or "",
                },
            )
            
            # Link team to group
            group.core_team = team
            group.save(update_fields=["core_team"])
            
        # First, check if student is already in another group in this category
        old_membership = CanvasGroupMembership.objects.filter(
            group__category=group.category, 
            user_id=student_id
        ).first()
        
        if old_membership and old_membership.group_id != group.id:
            # Remove from old group
            old_membership.delete()
            
            # If student had a team assignment, update it
            if student.team and student.team.canvas_group_link and student.team.canvas_group_link.category == group.category:
                # Only remove team assignment if it's in the same category
                student.team = None
                student.save(update_fields=["team"])
        
        # Create or update membership
        membership, created = CanvasGroupMembership.objects.update_or_create(
            group=group,
            user_id=student_id,
            defaults={
                "name": enrollment.user_name,
                "email": enrollment.email,
                "student": student,
            },
        )
        
        # Assign student to team
        student.team = team
        student.save(update_fields=["team"])
        
        return JsonResponse({
            "success": True,
            "message": f"Student added to {group.name}",
            "student": {
                "id": student.id,
                "name": student.get_full_name(),
                "email": student.email,
            },
            "group": {
                "id": group.id,
                "name": group.name,
            },
            "created": created,
        })
        
    except Exception as e:
        logger.error(f"Error adding student to group: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_POST
def remove_student_from_group(request, course_id, category_id):
    """
    Remove a student from their group in a category.
    This supports dragging a student to the unassigned area.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Authentication required"}, status=401)

    try:
        # Parse request data
        data = json.loads(request.body)
        student_id = data.get("student_id")
        
        if not student_id:
            return JsonResponse({"success": False, "error": "Student ID is required"}, status=400)
            
        # Get the necessary objects
        integration = get_integration_for_user(request.user)
        if not integration:
            return JsonResponse({"success": False, "error": "Canvas integration not set up"}, status=403)
        
        course = get_object_or_404(CanvasCourse, canvas_id=course_id, integration=integration)
        category = get_object_or_404(CanvasGroupCategory, id=category_id, course=course)
        
        # Find the student enrollment
        enrollment = get_object_or_404(CanvasEnrollment, course=course, user_id=student_id)
        
        # Get student record
        student = enrollment.student
        if not student:
            return JsonResponse({"success": False, "error": "Student not found in local database"}, status=404)
        
        # Find group membership
        membership = CanvasGroupMembership.objects.filter(
            group__category=category, 
            user_id=student_id
        ).first()
        
        if not membership:
            return JsonResponse({"success": True, "message": "Student was not in any group in this category"})
        
        # Get the group name for the response
        group_name = membership.group.name
        
        # Remove from group
        membership.delete()
        
        # If student has a team assignment in this category, remove it
        if student.team and student.team.canvas_group_link and student.team.canvas_group_link.category == category:
            student.team = None
            student.save(update_fields=["team"])
        
        return JsonResponse({
            "success": True,
            "message": f"Student removed from {group_name}",
            "student": {
                "id": student.id,
                "name": student.get_full_name(),
                "email": student.email,
            },
        })
        
    except Exception as e:
        logger.error(f"Error removing student from group: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_POST
def batch_assign_students(request, course_id, category_id):
    """
    Batch assign students to groups based on drag-and-drop changes.
    This supports the SortableJS implementation's batch save operation.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Authentication required"}, status=401)

    try:
        # Parse request data
        data = json.loads(request.body)
        changes = data.get("changes", [])
        
        if not changes:
            return JsonResponse({
                "success": True,
                "message": "No changes to apply",
                "applied": 0,
            })
            
        # Get the necessary objects
        integration = get_integration_for_user(request.user)
        if not integration:
            return JsonResponse({"success": False, "error": "Canvas integration not set up"}, status=403)
        
        course = get_object_or_404(CanvasCourse, canvas_id=course_id, integration=integration)
        category = get_object_or_404(CanvasGroupCategory, id=category_id, course=course)
        
        # Track statistics for response
        applied_count = 0
        errors = []
        
        # Process each change
        for change in changes:
            student_id = change.get("student_id")
            new_group_id = change.get("new_group_id")  # Can be None for unassign
            
            try:
                # Find student enrollment
                enrollment = CanvasEnrollment.objects.get(course=course, user_id=student_id)
                
                # Case 1: Remove from group (new_group_id is None)
                if new_group_id is None:
                    # Find and remove existing membership
                    membership = CanvasGroupMembership.objects.filter(
                        group__category=category, 
                        user_id=student_id
                    ).first()
                    
                    if membership:
                        # Get student
                        student = enrollment.student
                        if student:
                            # If student has a team assignment in this category, remove it
                            if student.team and student.team.canvas_group_link and student.team.canvas_group_link.category == category:
                                student.team = None
                                student.save(update_fields=["team"])
                        
                        # Remove membership
                        membership.delete()
                        applied_count += 1
                
                # Case 2: Assign to group
                else:
                    # Get the group
                    group = CanvasGroup.objects.get(id=new_group_id, category=category)
                    
                    # Get or create student record
                    student = enrollment.student
                    if not student:
                        # Parse user name
                        user_name_parts = enrollment.user_name.split()
                        first_name = user_name_parts[0] if user_name_parts else "Unknown"
                        last_name = " ".join(user_name_parts[1:]) if len(user_name_parts) > 1 else ""
                        
                        # Create the student record
                        student, _ = Student.objects.update_or_create(
                            canvas_user_id=student_id,
                            defaults={
                                "email": enrollment.email or f"canvas-user-{student_id}@example.com",
                                "first_name": first_name,
                                "last_name": last_name,
                            },
                        )
                        
                        # Link student to enrollment
                        enrollment.student = student
                        enrollment.save(update_fields=["student"])
                    
                    # Get or create team link
                    team = group.core_team
                    if not team:
                        team, _ = Team.objects.update_or_create(
                            canvas_group_id=group.canvas_id,
                            canvas_course=course,
                            defaults={
                                "name": group.name[:100],
                                "description": group.description or "",
                            },
                        )
                        
                        # Link team to group
                        group.core_team = team
                        group.save(update_fields=["core_team"])
                    
                    # Remove from any existing group in this category
                    CanvasGroupMembership.objects.filter(
                        group__category=category, 
                        user_id=student_id
                    ).delete()
                    
                    # Create new membership
                    CanvasGroupMembership.objects.create(
                        group=group,
                        user_id=student_id,
                        name=enrollment.user_name,
                        email=enrollment.email,
                        student=student,
                    )
                    
                    # Assign student to team
                    student.team = team
                    student.save(update_fields=["team"])
                    applied_count += 1
            
            except Exception as e:
                errors.append({
                    "student_id": student_id,
                    "error": str(e)
                })
                logger.error(f"Error applying change for student {student_id}: {str(e)}")
        
        # Push changes to Canvas if needed (async)
        if applied_count > 0:
            try:
                # This is async, so we don't await it - it happens in the background
                push_team_assignments_to_canvas(integration, course_id, request.user.id)
            except Exception as e:
                logger.error(f"Error pushing changes to Canvas: {str(e)}")
        
        return JsonResponse({
            "success": True,
            "message": f"Applied {applied_count} changes successfully",
            "applied": applied_count,
            "errors": errors,
        })
        
    except Exception as e:
        logger.error(f"Error batch assigning students: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_POST
def random_assign_students(request, course_id, category_id):
    """
    Randomly assign unassigned students to groups in a category.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Authentication required"}, status=401)

    try:
        # Get the necessary objects
        integration = get_integration_for_user(request.user)
        if not integration:
            return JsonResponse({"success": False, "error": "Canvas integration not set up"}, status=403)
        
        course = get_object_or_404(CanvasCourse, canvas_id=course_id, integration=integration)
        category = get_object_or_404(CanvasGroupCategory, id=category_id, course=course)
        
        # Get all groups in this category
        groups = list(CanvasGroup.objects.filter(category=category))
        if not groups:
            return JsonResponse({"success": False, "error": "No groups found in this category"}, status=400)
        
        # Get unassigned students
        assigned_user_ids = CanvasGroupMembership.objects.filter(
            group__category=category
        ).values_list("user_id", flat=True)
        
        unassigned_enrollments = CanvasEnrollment.objects.filter(
            course=course,
            role="StudentEnrollment"
        ).exclude(
            user_id__in=assigned_user_ids
        )
        
        if not unassigned_enrollments:
            return JsonResponse({
                "success": True,
                "message": "No unassigned students found",
                "assigned_count": 0,
            })
        
        # Prepare core team links for all groups
        for group in groups:
            if not group.core_team:
                # Create team for this group
                team, _ = Team.objects.update_or_create(
                    canvas_group_id=group.canvas_id,
                    canvas_course=course,
                    defaults={
                        "name": group.name[:100],
                        "description": group.description or "",
                    },
                )
                
                # Link team to group
                group.core_team = team
                group.save(update_fields=["core_team"])
        
        # Shuffle enrollments
        enrollment_list = list(unassigned_enrollments)
        random.shuffle(enrollment_list)
        
        # Track assignments
        assignments_count = 0
        
        # Distribute evenly
        for i, enrollment in enumerate(enrollment_list):
            # Pick group in round-robin fashion
            group_index = i % len(groups)
            group = groups[group_index]
            
            try:
                # Get or create student
                student = enrollment.student
                if not student:
                    # Parse user name
                    user_name_parts = enrollment.user_name.split()
                    first_name = user_name_parts[0] if user_name_parts else "Unknown"
                    last_name = " ".join(user_name_parts[1:]) if len(user_name_parts) > 1 else ""
                    
                    # Create student record
                    student, _ = Student.objects.update_or_create(
                        canvas_user_id=enrollment.user_id,
                        defaults={
                            "email": enrollment.email or f"canvas-user-{enrollment.user_id}@example.com",
                            "first_name": first_name,
                            "last_name": last_name,
                        },
                    )
                    
                    # Link to enrollment
                    enrollment.student = student
                    enrollment.save(update_fields=["student"])
                
                # Create membership
                CanvasGroupMembership.objects.create(
                    group=group,
                    user_id=enrollment.user_id,
                    name=enrollment.user_name,
                    email=enrollment.email,
                    student=student,
                )
                
                # Assign team
                student.team = group.core_team
                student.save(update_fields=["team"])
                
                assignments_count += 1
            except Exception as e:
                logger.error(f"Error assigning student {enrollment.user_id} to group {group.id}: {str(e)}")
                continue
        
        # Push changes to Canvas if needed (async)
        if assignments_count > 0:
            try:
                # This is async, so we don't await it - it happens in the background
                push_team_assignments_to_canvas(integration, course_id, request.user.id)
            except Exception as e:
                logger.error(f"Error pushing changes to Canvas: {str(e)}")
        
        return JsonResponse({
            "success": True,
            "message": f"Randomly assigned {assignments_count} students to groups",
            "assigned_count": assignments_count,
        })
        
    except Exception as e:
        logger.error(f"Error randomly assigning students: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)