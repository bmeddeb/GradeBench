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
from asgiref.sync import sync_to_async

from lms.canvas.models import (
    CanvasCourse,
    CanvasEnrollment,
    CanvasGroup,
    CanvasGroupCategory,
    CanvasGroupMembership,
)
from core.models import Student, Team
from .views import get_integration_for_user, async_get_integration_for_user
from .sync_utils import (
    async_create_group_category,
    async_update_group_category,
    async_create_group,
    async_update_group,
    async_delete_group,
    async_delete_group_category,
    async_push_group_memberships,
    async_push_all_group_memberships
)

logger = logging.getLogger(__name__)


@login_required
@require_POST
async def add_student_to_group(request, course_id, group_id):
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

        # Get the necessary objects asynchronously
        integration = await async_get_integration_for_user(request.user)
        if not integration:
            return JsonResponse({"success": False, "error": "Canvas integration not set up"}, status=403)

        course = await sync_to_async(get_object_or_404)(
            CanvasCourse, canvas_id=course_id, integration=integration)
        group = await sync_to_async(get_object_or_404)(CanvasGroup, id=group_id)

        if group.category.course != course:
            return JsonResponse({"success": False, "error": "Group does not belong to this course"}, status=403)

        # Find the student enrollment
        enrollment = await sync_to_async(get_object_or_404)(
            CanvasEnrollment, course=course, user_id=student_id)

        # Get or create student record
        student = enrollment.student
        if not student:
            # Parse user name
            user_name_parts = enrollment.user_name.split()
            first_name = user_name_parts[0] if user_name_parts else "Unknown"
            last_name = " ".join(user_name_parts[1:]) if len(
                user_name_parts) > 1 else ""

            # Create the student record
            student, created = await sync_to_async(Student.objects.update_or_create)(
                canvas_user_id=student_id,
                defaults={
                    "email": enrollment.email or f"canvas-user-{student_id}@example.com",
                    "first_name": first_name,
                    "last_name": last_name,
                },
            )

            # Link student to enrollment
            enrollment.student = student
            await sync_to_async(lambda: enrollment.save(update_fields=["student"]))()

        # Get or create team link
        team = group.core_team
        if not team:
            team, created = await sync_to_async(Team.objects.update_or_create)(
                canvas_group_id=group.canvas_id,
                canvas_course=course,
                defaults={
                    "name": group.name[:100],
                    "description": group.description or "",
                },
            )

            # Link team to group
            group.core_team = team
            await sync_to_async(lambda: group.save(update_fields=["core_team"]))()

        # First, check if student is already in another group in this category
        old_membership = await sync_to_async(lambda: CanvasGroupMembership.objects.filter(
            group__category=group.category,
            user_id=student_id
        ).first())()

        if old_membership and old_membership.group_id != group.id:
            # Remove from old group
            await sync_to_async(old_membership.delete)()

            # If student had a team assignment, update it
            if student.team and student.team.canvas_group_link and student.team.canvas_group_link.category == group.category:
                # Only remove team assignment if it's in the same category
                student.team = None
                await sync_to_async(lambda: student.save(update_fields=["team"]))()

        # Create or update membership
        membership, created = await sync_to_async(CanvasGroupMembership.objects.update_or_create)(
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
        await sync_to_async(lambda: student.save(update_fields=["team"]))()

        # Push the updated membership list to Canvas
        # Get all user IDs for this group
        all_memberships = await sync_to_async(lambda: CanvasGroupMembership.objects.filter(group=group))()
        user_ids = [m.user_id for m in await sync_to_async(list)(all_memberships)]

        # Push to Canvas asynchronously
        await async_push_group_memberships(integration, group.canvas_id, user_ids)

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
async def remove_student_from_group(request, course_id, category_id):
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

        # Get the necessary objects asynchronously
        integration = await async_get_integration_for_user(request.user)
        if not integration:
            return JsonResponse({"success": False, "error": "Canvas integration not set up"}, status=403)

        course = await sync_to_async(get_object_or_404)(
            CanvasCourse, canvas_id=course_id, integration=integration)
        category = await sync_to_async(get_object_or_404)(
            CanvasGroupCategory, id=category_id, course=course)

        # Find the student enrollment
        enrollment = await sync_to_async(get_object_or_404)(
            CanvasEnrollment, course=course, user_id=student_id)

        # Get student record
        student = enrollment.student
        if not student:
            return JsonResponse({"success": False, "error": "Student not found in local database"}, status=404)

        # Find group membership
        membership = await sync_to_async(lambda: CanvasGroupMembership.objects.filter(
            group__category=category,
            user_id=student_id
        ).first())()

        if not membership:
            return JsonResponse({"success": True, "message": "Student was not in any group in this category"})

        # Get the group name for the response
        group_name = membership.group.name
        group = membership.group

        # Remove from group
        await sync_to_async(membership.delete)()

        # If student has a team assignment in this category, remove it
        if student.team and student.team.canvas_group_link and student.team.canvas_group_link.category == category:
            student.team = None
            await sync_to_async(lambda: student.save(update_fields=["team"]))()

        # Push the updated membership list to Canvas
        # Get all user IDs for this group
        all_memberships = await sync_to_async(lambda: CanvasGroupMembership.objects.filter(group=group))()
        user_ids = [m.user_id for m in await sync_to_async(list)(all_memberships)]

        # Push to Canvas asynchronously
        await async_push_group_memberships(integration, group.canvas_id, user_ids)

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
async def batch_assign_students(request, course_id, category_id):
    """
    Batch assign students to groups based on a submitted mapping.
    This is used for the batch assignment form.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Authentication required"}, status=401)

    try:
        # Parse request data
        data = json.loads(request.body)
        assignments = data.get("assignments", [])

        if not assignments:
            return JsonResponse({"success": False, "error": "No assignments provided"}, status=400)

        # Get the necessary objects asynchronously
        integration = await async_get_integration_for_user(request.user)
        if not integration:
            return JsonResponse({"success": False, "error": "Canvas integration not set up"}, status=403)

        course = await sync_to_async(get_object_or_404)(
            CanvasCourse, canvas_id=course_id, integration=integration)
        category = await sync_to_async(get_object_or_404)(
            CanvasGroupCategory, id=category_id, course=course)

        # Track application counts and errors
        applied_count = 0
        errors = []
        modified_groups = set()

        # Process each assignment
        for assignment in assignments:
            student_id = assignment.get("student_id")
            group_id = assignment.get("group_id")
            remove = assignment.get("remove", False)

            # Skip entries without student_id
            if not student_id:
                errors.append({"error": "Student ID is required", "data": assignment})
                continue

            try:
                # Find the student enrollment
                enrollment = await sync_to_async(lambda: CanvasEnrollment.objects.filter(
                    course=course, user_id=student_id
                ).first())()

                if not enrollment:
                    errors.append({"error": f"Student with ID {student_id} not found in course", "data": assignment})
                    continue

                # Get student record
                student = enrollment.student
                if not student:
                    errors.append({"error": f"Student record not found for ID {student_id}", "data": assignment})
                    continue

                # Check if we need to remove from a group
                if remove:
                    # Find existing membership
                    membership = await sync_to_async(lambda: CanvasGroupMembership.objects.filter(
                        group__category=category,
                        user_id=student_id
                    ).first())()

                    if membership:
                        # Track the group for later synchronization
                        modified_groups.add(membership.group)

                        # Delete the membership
                        await sync_to_async(membership.delete)()

                        # Remove team assignment if applicable
                        if student.team and student.team.canvas_group_link and student.team.canvas_group_link.category == category:
                            student.team = None
                            await sync_to_async(lambda: student.save(update_fields=["team"]))()

                        applied_count += 1
                    else:
                        # Student wasn't in a group, nothing to do
                        applied_count += 1

                # Otherwise we're adding to a group
                elif group_id:
                    # Get the target group
                    group = await sync_to_async(lambda: CanvasGroup.objects.filter(
                        id=group_id, category=category
                    ).first())()

                    if not group:
                        errors.append({"error": f"Group with ID {group_id} not found in category", "data": assignment})
                        continue

                    # Remove from any existing group in this category
                    old_membership = await sync_to_async(lambda: CanvasGroupMembership.objects.filter(
                        group__category=category,
                        user_id=student_id
                    ).first())()

                    if old_membership and old_membership.group_id != group.id:
                        # Track the old group for later synchronization if it's different
                        modified_groups.add(old_membership.group)

                        # Remove from old group
                        await sync_to_async(old_membership.delete)()

                    # Ensure the group has a team link
                    if not group.core_team:
                        team, created = await sync_to_async(Team.objects.update_or_create)(
                            canvas_group_id=group.canvas_id,
                            canvas_course=course,
                            defaults={
                                "name": group.name[:100],
                                "description": group.description or "",
                            },
                        )

                        # Link team to group
                        group.core_team = team
                        await sync_to_async(lambda: group.save(update_fields=["core_team"]))()
                    else:
                        team = group.core_team

                    # Create or update the membership
                    membership, created = await sync_to_async(CanvasGroupMembership.objects.update_or_create)(
                        group=group,
                        user_id=student_id,
                        defaults={
                            "name": enrollment.user_name,
                            "email": enrollment.email,
                            "student": student,
                        },
                    )

                    # Update team assignment
                    student.team = team
                    await sync_to_async(lambda: student.save(update_fields=["team"]))()

                    # Track the modified group
                    modified_groups.add(group)
                    applied_count += 1

            except Exception as e:
                logger.error(f"Error processing assignment {assignment}: {str(e)}")
                errors.append({"error": str(e), "data": assignment})

        # Push the changes to all modified groups
        for group in modified_groups:
            try:
                # Get all user IDs for this group
                all_memberships = await sync_to_async(lambda: CanvasGroupMembership.objects.filter(group=group))()
                user_ids = [m.user_id for m in await sync_to_async(list)(all_memberships)]

                # Push to Canvas asynchronously
                await async_push_group_memberships(integration, group.canvas_id, user_ids)
            except Exception as e:
                logger.error(f"Error pushing memberships for group {group.name}: {str(e)}")
                errors.append({
                    "group_id": group.id,
                    "group_name": group.name,
                    "error": f"Failed to push to Canvas: {str(e)}"
                })

        # Return success response
        return JsonResponse({
            "success": True,
            "message": f"Applied {applied_count} changes successfully",
            "applied_count": applied_count,
            "errors": errors,
            "groups_modified": len(modified_groups),
        })

    except Exception as e:
        logger.error(f"Error in batch assignment: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
@require_POST
async def random_assign_students(request, course_id, category_id):
    """
    Randomly assign unassigned students to groups in a category.
    """
    if not request.user.is_authenticated:
        return JsonResponse({"success": False, "error": "Authentication required"}, status=401)

    try:
        # Get the necessary objects asynchronously
        integration = await async_get_integration_for_user(request.user)
        if not integration:
            return JsonResponse({"success": False, "error": "Canvas integration not set up"}, status=403)

        course = await sync_to_async(get_object_or_404)(
            CanvasCourse, canvas_id=course_id, integration=integration)
        category = await sync_to_async(get_object_or_404)(
            CanvasGroupCategory, id=category_id, course=course)

        # Get all groups in this category
        groups_queryset = CanvasGroup.objects.filter(category=category)
        groups = await sync_to_async(list)(groups_queryset)
        
        if not groups:
            return JsonResponse({"success": False, "error": "No groups found in this category"}, status=400)

        # Get unassigned students
        assigned_user_ids = await sync_to_async(lambda: CanvasGroupMembership.objects.filter(
            group__category=category
        ).values_list("user_id", flat=True))()
        
        unassigned_enrollments_queryset = CanvasEnrollment.objects.filter(
            course=course,
            role="StudentEnrollment"
        ).exclude(
            user_id__in=assigned_user_ids
        )
        
        unassigned_enrollments = await sync_to_async(list)(unassigned_enrollments_queryset)

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
                team, _ = await sync_to_async(Team.objects.update_or_create)(
                    canvas_group_id=group.canvas_id,
                    canvas_course=course,
                    defaults={
                        "name": group.name[:100],
                        "description": group.description or "",
                    },
                )

                # Link team to group
                group.core_team = team
                await sync_to_async(lambda: group.save(update_fields=["core_team"]))()

        # Shuffle enrollments
        enrollment_list = list(unassigned_enrollments)
        random.shuffle(enrollment_list)

        # Track assignments and modified groups
        assignments_count = 0
        modified_groups = set()

        # Distribute evenly
        for i, enrollment in enumerate(enrollment_list):
            # Pick group in round-robin fashion
            group_index = i % len(groups)
            group = groups[group_index]

            # Track the group as modified
            modified_groups.add(group)

            try:
                # Get or create student
                student = enrollment.student
                if not student:
                    # Parse user name
                    user_name_parts = enrollment.user_name.split()
                    first_name = user_name_parts[0] if user_name_parts else "Unknown"
                    last_name = " ".join(user_name_parts[1:]) if len(
                        user_name_parts) > 1 else ""

                    # Create student record
                    student, _ = await sync_to_async(Student.objects.update_or_create)(
                        canvas_user_id=enrollment.user_id,
                        defaults={
                            "email": enrollment.email or f"canvas-user-{enrollment.user_id}@example.com",
                            "first_name": first_name,
                            "last_name": last_name,
                        },
                    )

                    # Link student to enrollment
                    enrollment.student = student
                    await sync_to_async(lambda: enrollment.save(update_fields=["student"]))()

                # Create membership
                await sync_to_async(CanvasGroupMembership.objects.update_or_create)(
                    group=group,
                    user_id=enrollment.user_id,
                    defaults={
                        "name": enrollment.user_name,
                        "email": enrollment.email,
                        "student": student,
                    },
                )

                # Update team assignment
                student.team = group.core_team
                await sync_to_async(lambda: student.save(update_fields=["team"]))()

                assignments_count += 1
            except Exception as e:
                logger.error(f"Error assigning student {enrollment.user_name}: {str(e)}")

        # Push memberships to Canvas for all modified groups
        for group in modified_groups:
            try:
                # Get all user IDs for this group
                all_memberships = await sync_to_async(lambda: CanvasGroupMembership.objects.filter(group=group))()
                user_ids = [m.user_id for m in await sync_to_async(list)(all_memberships)]

                # Push to Canvas asynchronously
                await async_push_group_memberships(integration, group.canvas_id, user_ids)
            except Exception as e:
                logger.error(f"Error pushing memberships for group {group.name}: {str(e)}")

        return JsonResponse({
            "success": True,
            "message": f"Randomly assigned {assignments_count} students to {len(modified_groups)} groups",
            "assigned_count": assignments_count,
            "groups_count": len(modified_groups),
        })

    except Exception as e:
        logger.error(f"Error randomly assigning students: {str(e)}")
        return JsonResponse({"success": False, "error": str(e)}, status=500)