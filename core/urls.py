# core/urls.py
from django.urls import path, include
# (to be modularized)
from .views.auth import HomeView, LoginView, ProfileView, UpdateProfileAjaxView, StyleguideView, LogoutView
from .views.github import disconnect_github, async_github_profile
from .views.calendar import CalendarEventsView, UploadICSView
from .views.wizard import WizardView

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("login/", LoginView.as_view(), name="login"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("disconnect-github/", disconnect_github, name="disconnect_github"),
    path("api/github-profile/", async_github_profile, name="github_profile"),
    path("api/update-profile/", UpdateProfileAjaxView.as_view(),
         name="update_profile_async"),
    path("canvas/", include("lms.canvas.urls")),
    # Calendar API routes
    path("api/calendar/events/", CalendarEventsView.as_view(),
         name="calendar_events"),
    path("api/calendar/upload-ics/", UploadICSView.as_view(), name="upload_ics"),
    path("styleguide/", StyleguideView.as_view(), name="styleguide"),
    # Canvas Group to Team Sync Wizard
    path("wizard/", WizardView.as_view(), name="wizard_main"),
]
