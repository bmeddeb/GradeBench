from django.urls import path
from . import views

# Import Phase 3 views for SortableJS implementation
from .views_group_assignment import (
    add_student_to_group,
    remove_student_from_group,
    batch_assign_students,
    random_assign_students,
)

urlpatterns = [
    # Main Canvas dashboard
    path("", views.canvas_dashboard, name="canvas_dashboard"),
    # Setup
    path("setup/", views.canvas_setup, name="canvas_setup"),
    # Sync all courses
    path("sync/", views.canvas_sync, name="canvas_sync"),
    # List available courses for selection (AJAX)
    path(
        "list_available_courses/",
        views.canvas_list_available_courses,
        name="canvas_list_available_courses",
    ),
    # Sync selected courses (AJAX)
    path(
        "sync_selected_courses/",
        views.canvas_sync_selected_courses,
        name="canvas_sync_selected_courses",
    ),
    # Get sync progress (AJAX)
    path("sync_progress/", views.canvas_sync_progress,
         name="canvas_sync_progress"),
    # Courses list
    path("course/", views.canvas_courses_list, name="canvas_courses_list"),
    # Students list
    path("student/", views.canvas_students_list, name="canvas_students_list"),
    # Assignments list
    path("assignment/", views.canvas_assignments_list,
         name="canvas_assignments_list"),
    # Course detail
    path("course/<int:course_id>/", views.course_detail,
         name="canvas_course_detail"),
    # Delete course
    path(
        "course/<int:course_id>/delete/",
        views.canvas_delete_course,
        name="canvas_delete_course",
    ),
    # Sync single course
    path(
        "course/<int:course_id>/sync/",
        views.canvas_sync_single_course,
        name="canvas_sync_course",
    ),
    # Assignment detail
    path(
        "course/<int:course_id>/assignment/<int:assignment_id>/",
        views.assignment_detail,
        name="canvas_assignment_detail",
    ),
    # Student detail
    path(
        "course/<int:course_id>/student/<int:user_id>/",
        views.student_detail,
        name="canvas_student_detail",
    ),

    # Group Management URLs

    # Course groups overview
    path(
        "course/<int:course_id>/groups/",
        views.course_groups,
        name="canvas_course_groups",
    ),
    # Sync course groups
    path(
        "course/<int:course_id>/sync_groups/",
        views.canvas_sync_course_groups,
        name="canvas_sync_course_groups",
    ),
    # Push all group memberships to Canvas
    path(
        "course/<int:course_id>/push_group_memberships/",
        views.push_course_group_memberships,
        name="canvas_push_group_memberships",
    ),
    # Group set details (AJAX)
    path(
        "course/<int:course_id>/group_set/<int:group_set_id>/details/",
        views.group_set_detail,
        name="canvas_group_set_detail",
    ),
    # Create group set
    path(
        "course/<int:course_id>/group_set/create/",
        views.create_group_set,
        name="canvas_create_group_set",
    ),
    # Edit group set
    path(
        "course/<int:course_id>/group_set/<int:group_set_id>/edit/",
        views.edit_group_set,
        name="canvas_edit_group_set",
    ),
    # Delete group set
    path(
        "course/<int:course_id>/group_set/<int:group_set_id>/delete/",
        views.delete_group_set,
        name="canvas_delete_group_set",
    ),
    # Create group
    path(
        "course/<int:course_id>/group_set/<int:group_set_id>/create_group/",
        views.create_group,
        name="canvas_create_group",
    ),
    # Edit group
    path(
        "course/<int:course_id>/group/<int:group_id>/edit/",
        views.edit_group,
        name="canvas_edit_group",
    ),
    # Delete group
    path(
        "course/<int:course_id>/group/<int:group_id>/delete/",
        views.delete_group,
        name="canvas_delete_group",
    ),

    # Group Assignment URLs (AJAX)

    # Add student to group (AJAX)
    path(
        "course/<int:course_id>/group/<int:group_id>/add_student/",
        add_student_to_group,
        name="canvas_add_student_to_group",
    ),
    # Remove student from group (AJAX)
    path(
        "course/<int:course_id>/group_set/<int:category_id>/remove_student/",
        remove_student_from_group,
        name="canvas_remove_student_from_group",
    ),
    # Batch assignment of students (AJAX)
    path(
        "course/<int:course_id>/group_set/<int:category_id>/batch_assign/",
        batch_assign_students,
        name="canvas_batch_assign_students",
    ),
    # Random assignment of students (AJAX)
    path(
        "course/<int:course_id>/group_set/<int:category_id>/random_assign/",
        random_assign_students,
        name="canvas_random_assign_students",
    ),
]
