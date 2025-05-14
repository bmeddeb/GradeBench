# core/views/__init__.py
# Expose modularized views for easy import
from .wizard import wizard_view
from .calendar import calendar_events, upload_ics
from .github import disconnect_github, async_github_profile
from .auth import home, login, profile, update_profile_ajax, styleguide, logout_view
