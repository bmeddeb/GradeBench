"""
Legacy views module for Canvas integration

This module preserves backward compatibility for existing imports.
All new code should import from the views package directly.
"""

import logging

# Re-export the get_integration_for_user function
def get_integration_for_user(user):
    """Get or create a Canvas integration for the user"""
    from .models import CanvasIntegration
    try:
        integration = CanvasIntegration.objects.get(user=user)
        return integration
    except CanvasIntegration.DoesNotExist:
        return None

# Import all view functions from the views package for backward compatibility
from .views.courses import (
    canvas_courses_list,
    course_detail,
    canvas_dashboard,
    canvas_delete_course,
)

from .views.students import (
    canvas_students_list,
    student_detail,
)

from .views.assignments import (
    canvas_assignments_list,
    assignment_detail,
)

from .views.setup import (
    canvas_setup,
    canvas_list_available_courses,
)

from .views.sync import (
    canvas_sync,
    canvas_sync_single_course,
    canvas_sync_progress,
    canvas_sync_batch_progress,
    canvas_sync_selected_courses,
    canvas_sync_course_groups,
)

from .views.groups import (
    course_groups,
    group_set_detail,
    create_group_set,
    edit_group_set,
    delete_group_set,
    create_group,
    edit_group,
    delete_group,
    push_course_group_memberships,
)

# Import special Ajax views from views_group_assignment since they're not in our modular structure yet
from .views_group_assignment import (
    add_student_to_group,
    remove_student_from_group,
    batch_assign_students,
    random_assign_students,
)

# Alias for backward compatibility
canvas_course_groups = course_groups