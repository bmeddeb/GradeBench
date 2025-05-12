"""
Phase 3: Canvas group student assignment views for SortableJS implementation
These view functions support the drag-and-drop functionality for assigning students to groups.
"""

import json
import logging
import random

from django.db import transaction
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
from .decorators import canvas_integration_required_json
from .utils import (
    get_or_create_student_from_enrollment,
    get_or_create_team_from_group,
    batch_assign_students_to_groups,
    get_json_error_response,
    get_json_success_response,
)
from .sync_utils import push_group_memberships_sync

logger = logging.getLogger(__name__)


@require_POST
@canvas_integration_required_json
def add_student_to_group(request, course_id, group_id):
    """
    Add a student to a Canvas group via AJAX.
    This supports individual drag-and-drop assignments.
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        student_id = data.get("student_id")

        if not student_id:
            return JsonResponse(
                get_json_error_response("Student ID is required"), 
                status=400
            )

        # Get the necessary objects
        integration = request.canvas_integration
        course = get_object_or_404(
            CanvasCourse, canvas_id=course_id, integration=integration)
        group = get_object_or_404(CanvasGroup, id=group_id)

        if group.category.course != course:
            return JsonResponse(
                get_json_error_response("Group does not belong to this course"), 
                status=403
            )

        # Find the student enrollment
        enrollment = get_object_or_404(
            CanvasEnrollment, course=course, user_id=student_id)

        # Get or create student record
        student, student_created = get_or_create_student_from_enrollment(enrollment)

        # Get or create team link
        team, team_created = get_or_create_team_from_group(group, course)

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

        # Get all user IDs for this group
        all_memberships = CanvasGroupMembership.objects.filter(group=group)
        user_ids = [m.user_id for m in all_memberships]

        # Push to Canvas
        push_group_memberships_sync(integration, group.canvas_id, user_ids)

        return JsonResponse(get_json_success_response(
            f"Student added to {group.name}",
            {
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
            }
        ))

    except Exception as e:
        logger.error(f"Error adding student to group: {str(e)}")
        return JsonResponse(get_json_error_response(str(e)), status=500)


@require_POST
@canvas_integration_required_json
def remove_student_from_group(request, course_id, category_id):
    """
    Remove a student from their group in a category.
    This supports dragging a student to the unassigned area.
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        student_id = data.get("student_id")

        if not student_id:
            return JsonResponse(
                get_json_error_response("Student ID is required"), 
                status=400
            )

        # Get the necessary objects
        integration = request.canvas_integration
        course = get_object_or_404(
            CanvasCourse, canvas_id=course_id, integration=integration)
        category = get_object_or_404(
            CanvasGroupCategory, id=category_id, course=course)

        # Find the student enrollment
        enrollment = get_object_or_404(
            CanvasEnrollment, course=course, user_id=student_id)

        # Get student record
        student = enrollment.student
        if not student:
            return JsonResponse(
                get_json_error_response("Student not found in local database"), 
                status=404
            )

        # Find group membership
        membership = CanvasGroupMembership.objects.filter(
            group__category=category,
            user_id=student_id
        ).first()

        if not membership:
            return JsonResponse(get_json_success_response(
                "Student was not in any group in this category"
            ))

        # Get the group name for the response
        group_name = membership.group.name
        group = membership.group

        # Remove from group
        membership.delete()

        # If student has a team assignment in this category, remove it
        if student.team and student.team.canvas_group_link and student.team.canvas_group_link.category == category:
            student.team = None
            student.save(update_fields=["team"])

        # Get all user IDs for this group
        all_memberships = CanvasGroupMembership.objects.filter(group=group)
        user_ids = [m.user_id for m in all_memberships]

        # Push to Canvas
        push_group_memberships_sync(integration, group.canvas_id, user_ids)

        return JsonResponse(get_json_success_response(
            f"Student removed from {group_name}",
            {
                "student": {
                    "id": student.id,
                    "name": student.get_full_name(),
                    "email": student.email,
                },
            }
        ))

    except Exception as e:
        logger.error(f"Error removing student from group: {str(e)}")
        return JsonResponse(get_json_error_response(str(e)), status=500)


@require_POST
@canvas_integration_required_json
@transaction.atomic
def batch_assign_students(request, course_id, category_id):
    """
    Batch assign students to groups based on drag-and-drop changes.
    This supports the SortableJS implementation's batch save operation.
    """
    try:
        # Parse request data
        data = json.loads(request.body)
        changes = data.get("changes", [])

        if not changes:
            return JsonResponse(get_json_success_response(
                "No changes to apply",
                {"applied": 0}
            ))

        # Get the necessary objects
        integration = request.canvas_integration
        course = get_object_or_404(
            CanvasCourse, canvas_id=course_id, integration=integration)
        category = get_object_or_404(
            CanvasGroupCategory, id=category_id, course=course)

        # Use our batch assign function
        result = batch_assign_students_to_groups(changes, course)
        
        # Push all modified groups to Canvas
        if result["modified_groups"]:
            errors = []
            # Push each modified group's memberships to Canvas
            for group in result["modified_groups"]:
                try:
                    # Get all memberships for this group
                    all_memberships = CanvasGroupMembership.objects.filter(
                        group=group)
                    user_ids = [m.user_id for m in all_memberships]

                    # Push to Canvas
                    push_group_memberships_sync(
                        integration, group.canvas_id, user_ids)
                except Exception as e:
                    logger.error(
                        f"Error pushing memberships for group {group.name}: {str(e)}")
                    errors.append({
                        "group_id": group.id,
                        "group_name": group.name,
                        "error": f"Failed to push to Canvas: {str(e)}"
                    })
                    
            # Add Canvas push errors to the result errors
            result["errors"].extend(errors)

        # Return success response
        return JsonResponse(get_json_success_response(
            f"Applied {result['applied_count']} changes successfully",
            {
                "applied_count": result["applied_count"],
                "errors": result["errors"],
                "groups_modified": len(result["modified_groups"]),
            }
        ))

    except Exception as e:
        logger.error(f"Error in batch assignment: {str(e)}")
        return JsonResponse(get_json_error_response(str(e)), status=500)


@require_POST
@canvas_integration_required_json
@transaction.atomic
def random_assign_students(request, course_id, category_id):
    """
    Randomly assign unassigned students to groups in a category.
    """
    try:
        # Get the necessary objects
        integration = request.canvas_integration
        course = get_object_or_404(
            CanvasCourse, canvas_id=course_id, integration=integration)
        category = get_object_or_404(
            CanvasGroupCategory, id=category_id, course=course)

        # Get all groups in this category
        groups = list(CanvasGroup.objects.filter(category=category))
        if not groups:
            return JsonResponse(
                get_json_error_response("No groups found in this category"), 
                status=400
            )

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
            return JsonResponse(get_json_success_response(
                "No unassigned students found",
                {"assigned_count": 0}
            ))

        # Prepare core team links for all groups
        for group in groups:
            get_or_create_team_from_group(group, course)

        # Shuffle enrollments
        enrollment_list = list(unassigned_enrollments)
        random.shuffle(enrollment_list)

        # Track assignments and modified groups
        assignments_count = 0
        modified_groups = set()

        # Build a list of changes for batch processing
        changes = []
        
        # Distribute evenly
        for i, enrollment in enumerate(enrollment_list):
            # Pick group in round-robin fashion
            group_index = i % len(groups)
            group = groups[group_index]
            
            # Add to changes
            changes.append({
                "student_id": enrollment.user_id,
                "new_group_id": group.id
            })

        # Process all changes in batch
        result = batch_assign_students_to_groups(changes, course)
        
        # Push memberships to Canvas for all modified groups
        if result["modified_groups"]:
            errors = []
            # Push each modified group's memberships to Canvas
            for group in result["modified_groups"]:
                try:
                    # Get all memberships for this group
                    all_memberships = CanvasGroupMembership.objects.filter(
                        group=group)
                    user_ids = [m.user_id for m in all_memberships]

                    # Push to Canvas
                    push_group_memberships_sync(
                        integration, group.canvas_id, user_ids)
                except Exception as e:
                    logger.error(
                        f"Error pushing memberships for group {group.name}: {str(e)}")
                    errors.append({
                        "group": group.name,
                        "error": str(e)
                    })

        return JsonResponse(get_json_success_response(
            f"Randomly assigned {result['applied_count']} students to groups",
            {
                "assigned_count": result["applied_count"],
                "groups_modified": len(result["modified_groups"]),
            }
        ))

    except Exception as e:
        logger.error(f"Error randomly assigning students: {str(e)}")
        return JsonResponse(get_json_error_response(str(e)), status=500)