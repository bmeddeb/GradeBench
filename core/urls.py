from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login, name='login'),
    path('profile/', views.profile, name='profile'),
    path('disconnect-github/', views.disconnect_github, name='disconnect_github'),
    path('api/github-profile/', views.async_github_profile, name='github_profile'),
    path('api/update-profile/', views.update_profile_ajax,
         name='update_profile_async'),
    path('canvas/', include('lms.canvas.urls')),
    
    # Calendar API routes
    path('api/calendar/events/', views.calendar_events, name='calendar_events'),
    path('api/calendar/upload-ics/', views.upload_ics, name='upload_ics'),
]