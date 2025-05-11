from django.urls import include, path

# Include Taiga-specific URLs
taiga_patterns = [
    # Add Taiga URLs here
    # path('projects/', views.project_list, name='project_list'),
    # path('projects/<int:project_id>/', views.project_detail, name='project_detail'),
]

# Main project_mgmt URL patterns
urlpatterns = [
    path("taiga/", include((taiga_patterns, "taiga"), namespace="taiga")),
    # Add other project management providers here, e.g.:
    # path('jira/', include((jira_patterns, 'jira'), namespace='jira')),
]
