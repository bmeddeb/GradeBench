from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('profile/', views.profile, name='profile'),
    path('disconnect-github/', views.disconnect_github, name='disconnect_github'),
    path('api/github-profile/', views.async_github_profile, name='github_profile'),
    path('api/update-profile/', views.update_profile_async,
         name='update_profile_async'),
]
