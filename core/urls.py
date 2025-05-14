# core/urls.py
from django.urls import path, include
# (to be modularized)
from .views.auth import home, login, profile, update_profile_ajax, styleguide, logout_view
from .views.github import disconnect_github, async_github_profile
from .views.calendar import calendar_events, upload_ics
from .views.wizard import wizard_view

urlpatterns = [
    path("", home, name="home"),
    path("login/", login, name="login"),
    path("profile/", profile, name="profile"),
    path("logout/", logout_view, name="logout"),
    path("disconnect-github/", disconnect_github, name="disconnect_github"),
    path("api/github-profile/", async_github_profile, name="github_profile"),
    path("api/update-profile/", update_profile_ajax, name="update_profile_async"),
    path("canvas/", include("lms.canvas.urls")),
    # Calendar API routes
    path("api/calendar/events/", calendar_events, name="calendar_events"),
    path("api/calendar/upload-ics/", upload_ics, name="upload_ics"),
    path("styleguide/", styleguide, name="styleguide"),
    # Canvas Group to Team Sync Wizard
    path("wizard/", wizard_view, name="wizard_main"),
]
