"""
Utility functions for Canvas-related operations
"""

import logging
from typing import Optional, Tuple, List, Dict, Any

from django.db import transaction
from django.db.models import QuerySet

from .models import (
    CanvasEnrollment,
    CanvasGroup,
    CanvasGroupMembership,
    CanvasCourse
)
from core.models import Student, Team

logger = logging.getLogger(__name__)


def get_or_create_student_from_enrollment(enrollment: CanvasEnrollment) -> Tuple[Student, bool]:
    """
    Gets or creates a Student object from a CanvasEnrollment.
    Returns (student, created) tuple.
    """
    student = enrollment.student
    if student:
        return student, False
        
    # Parse user name
    user_name_parts = enrollment.user_name.split()
    first_name = user_name_parts[0] if user_name_parts else "Unknown"
    last_name = " ".join(user_name_parts[1:]) if len(user_name_parts) > 1 else ""
    
    # Create the student record
    student, created = Student.objects.update_or_create(
        canvas_user_id=enrollment.user_id,
        defaults={
            "email": enrollment.email or f"canvas-user-{enrollment.user_id}@example.com",
            "first_name": first_name,
            "last_name": last_name,
        },
    )
    
    # Link student to enrollment if not already linked
    if enrollment.student != student:
        enrollment.student = student
        enrollment.save(update_fields=["student"])
    
    return student, created


def get_or_create_team_from_group(group: CanvasGroup, course: CanvasCourse) -> Tuple[Team, bool]:
    """
    Gets or creates a Team object from a CanvasGroup.
    Returns (team, created) tuple.
    """
    team = group.core_team
    if team:
        return team, False
        
    # Create team for this group
    team, created = Team.objects.update_or_create(
        canvas_group_id=group.canvas_id,
        canvas_course=course,
        defaults={
            "name": group.name[:100],
            "description": group.description or "",
        },
    )
    
    # Link team to group if not already linked
    if group.core_team != team:
        group.core_team = team
        group.save(update_fields=["core_team"])
    
    return team, created


def remove_student_from_group_category(student: Student, category_id: int) -> bool:
    """
    Removes a student from any group in the specified category.
    Returns True if student was removed from a group, False if they weren't in any group.
    """
    # Find current membership
    membership = CanvasGroupMembership.objects.filter(
        group__category_id=category_id,
        student=student
    ).first()
    
    if not membership:
        return False
        
    # Remove from group
    membership.delete()
    
    # If student has a team assignment in this category, remove it
    if student.team and student.team.canvas_group_link and student.team.canvas_group_link.category_id == category_id:
        student.team = None
        student.save(update_fields=["team"])
    
    return True


@transaction.atomic
def batch_assign_students_to_groups(
    changes: List[Dict[str, Any]], 
    course: CanvasCourse
) -> Dict[str, Any]:
    """
    Bulk assign students to groups based on a list of changes.
    Each change dict should contain:
    - student_id: Canvas user ID
    - new_group_id: Canvas group ID or None to remove from group
    
    Returns dict with:
    - applied_count: number of changes applied
    - errors: list of errors
    - modified_groups: set of modified CanvasGroup objects
    """
    applied_count = 0
    errors = []
    modified_groups = set()
    
    # Prefetch all enrollments to avoid N+1 queries
    student_ids = [change.get('student_id') for change in changes if change.get('student_id')]
    enrollments_by_id = {
        str(e.user_id): e for e in CanvasEnrollment.objects.filter(
            course=course, 
            user_id__in=student_ids
        ).select_related('student')
    }
    
    # Prefetch all groups to avoid N+1 queries
    group_ids = [change.get('new_group_id') for change in changes if change.get('new_group_id')]
    groups_by_id = {
        str(g.id): g for g in CanvasGroup.objects.filter(
            id__in=group_ids, 
            category__course=course
        ).select_related('category', 'core_team')
    }
    
    # Process each change
    for change in changes:
        student_id = str(change.get('student_id'))
        new_group_id = change.get('new_group_id')
        
        try:
            # Check if we have the enrollment
            enrollment = enrollments_by_id.get(student_id)
            if not enrollment:
                raise ValueError(f"Student enrollment not found for ID {student_id}")
            
            # Case 1: Remove from group
            if new_group_id is None:
                # Find existing memberships
                memberships = CanvasGroupMembership.objects.filter(
                    group__category__course=course,
                    user_id=student_id
                )
                
                for membership in memberships:
                    # Track the group being modified
                    modified_groups.add(membership.group)
                    
                    # Get student
                    student = enrollment.student
                    if student and student.team and student.team.canvas_group_link:
                        # Only remove team assignment if it's in this course
                        if student.team.canvas_group_link.category.course == course:
                            student.team = None
                            student.save(update_fields=["team"])
                
                # Delete all memberships
                if memberships:
                    memberships.delete()
                    applied_count += 1
            
            # Case 2: Assign to group
            else:
                group = groups_by_id.get(str(new_group_id))
                if not group:
                    raise ValueError(f"Group not found with ID {new_group_id}")
                
                # Track the group being modified
                modified_groups.add(group)
                
                # Get or create student record
                student, _ = get_or_create_student_from_enrollment(enrollment)
                
                # Get or create team link
                team, _ = get_or_create_team_from_group(group, course)
                
                # Remove from any existing group in this category
                old_memberships = CanvasGroupMembership.objects.filter(
                    group__category=group.category,
                    user_id=student_id
                )
                
                if old_memberships.exists():
                    for old_membership in old_memberships:
                        if old_membership.group_id != group.id:
                            modified_groups.add(old_membership.group)
                    old_memberships.delete()
                
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
            logger.error(f"Error applying change for student {student_id}: {str(e)}")
            errors.append({
                "student_id": student_id,
                "error": str(e)
            })
    
    return {
        "applied_count": applied_count,
        "errors": errors,
        "modified_groups": modified_groups
    }


def get_json_error_response(message: str, status_code: int = 400) -> Dict[str, Any]:
    """
    Returns a standardized error response dictionary
    """
    return {
        "success": False,
        "error": message,
        "status": "error"
    }


def get_json_success_response(message: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Returns a standardized success response dictionary
    """
    response = {
        "success": True,
        "message": message,
        "status": "success"
    }
    
    if data:
        response.update(data)
    
    return response