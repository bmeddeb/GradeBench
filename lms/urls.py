from django.urls import include, path

# Include Canvas-specific URLs
canvas_patterns = [
    # Add Canvas URLs here
    # path('courses/', views.course_list, name='course_list'),
    # path('courses/<int:course_id>/', views.course_detail, name='course_detail'),
]

# Main lms URL patterns
urlpatterns = [
    path("canvas/", include((canvas_patterns, "canvas"), namespace="canvas")),
    # Add other LMS providers here, e.g.:
    # path('blackboard/', include((blackboard_patterns, 'blackboard'), namespace='blackboard')),
]
