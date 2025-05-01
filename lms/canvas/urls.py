from django.urls import path
from . import views

urlpatterns = [
    # Main Canvas dashboard
    path('', views.canvas_dashboard, name='canvas_dashboard'),

    # Setup
    path('setup/', views.canvas_setup, name='canvas_setup'),

    # Sync all courses
    path('sync/', views.canvas_sync, name='canvas_sync'),

    # Course detail
    path('course/<int:course_id>/', views.course_detail,
         name='canvas_course_detail'),

    # Sync single course
    path('course/<int:course_id>/sync/',
         views.sync_single_course, name='canvas_sync_course'),

    # Assignment detail
    path('course/<int:course_id>/assignment/<int:assignment_id>/',
         views.assignment_detail, name='canvas_assignment_detail'),

    # Student detail
    path('course/<int:course_id>/student/<int:user_id>/',
         views.student_detail, name='canvas_student_detail'),
]
