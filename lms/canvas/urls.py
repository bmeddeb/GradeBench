from django.urls import path
from . import views

urlpatterns = [
    # Main Canvas dashboard
    path('', views.canvas_dashboard, name='canvas_dashboard'),

    # Setup
    path('setup/', views.canvas_setup, name='canvas_setup'),

    # Sync all courses
    path('sync/', views.canvas_sync, name='canvas_sync'),

    # List available courses for selection (AJAX)
    path('list_available_courses/', views.canvas_list_available_courses,
         name='canvas_list_available_courses'),

    # Sync selected courses (AJAX)
    path('sync_selected_courses/', views.canvas_sync_selected_courses,
         name='canvas_sync_selected_courses'),
         
    # Get sync progress (AJAX)
    path('sync_progress/', views.canvas_sync_progress,
         name='canvas_sync_progress'),

    # Courses list
    path('course/', views.canvas_courses_list, name='canvas_courses_list'),

    # Students list
    path('student/', views.canvas_students_list, name='canvas_students_list'),

    # Assignments list
    path('assignment/', views.canvas_assignments_list,
         name='canvas_assignments_list'),

    # Teams management list
    path('teams/', views.canvas_teams_list,
         name='canvas_teams_list'),

    # Course detail
    path('course/<int:course_id>/', views.course_detail,
         name='canvas_course_detail'),

    # Delete course
    path('course/<int:course_id>/delete/',
         views.canvas_delete_course, name='canvas_delete_course'),

    # Sync single course
    path('course/<int:course_id>/sync/',
         views.canvas_sync_single_course, name='canvas_sync_course'),

    # Assignment detail
    path('course/<int:course_id>/assignment/<int:assignment_id>/',
         views.assignment_detail, name='canvas_assignment_detail'),

    # Student detail
    path('course/<int:course_id>/student/<int:user_id>/',
         views.student_detail, name='canvas_student_detail'),

    # Team management with drag-and-drop interface
    path('course/<int:course_id>/manage-teams/',
         views.manage_teams, name='canvas_manage_teams'),

    # API endpoints for team management
    path('course/<int:course_id>/create-team/',
         views.create_team, name='canvas_create_team'),
    path('assign-student-to-team/',
         views.assign_student_to_team, name='canvas_assign_student_to_team'),
    path('remove-student-from-team/',
         views.remove_student_from_team, name='canvas_remove_student_from_team'),
    path('push-team-to-canvas/<int:team_id>/',
         views.push_team_to_canvas, name='canvas_push_team_to_canvas'),
    path('course/<int:course_id>/create-group-category/',
         views.create_canvas_group_category, name='canvas_create_group_category'),
]
