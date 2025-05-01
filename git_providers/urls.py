from django.urls import include, path

# Include GitHub-specific URLs
github_patterns = [
    # Add GitHub URLs here
    # path('repositories/', views.repository_list, name='repository_list'),
    # path('repositories/<str:owner>/<str:repo>/', views.repository_detail, name='repository_detail'),
]

# Main git_providers URL patterns
urlpatterns = [
    path('github/', include((github_patterns, 'github'), namespace='github')),
    # Add other git providers here, e.g.:
    # path('gitlab/', include((gitlab_patterns, 'gitlab'), namespace='gitlab')),
]
