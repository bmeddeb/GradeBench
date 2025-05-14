# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required
from social_django.models import UserSocialAuth
from django.contrib.auth.models import User
from .models import UserProfile, CalendarEvent
import httpx
import json
from asgiref.sync import sync_to_async
from django.core.exceptions import SynchronousOnlyOperation
from core.db import async_save
import io
from icalendar import Calendar
from django.utils import timezone
from datetime import datetime, timedelta
import pytz


@staff_member_required
def styleguide(request):
    """
    View for the style guide page.
    Only available to staff members.
    """
    return render(request, "styleguide.html")


# Create your views here.


@login_required
def home(request):
    """Home page view."""
    # Get all calendar events for the current user
    events = CalendarEvent.objects.filter(user=request.user)
    return render(
        request,
        "core/home.html",
        {
            "user": request.user,
            "profile": request.user.profile,
        },
    )


def login(request):
    """Login page view."""
    if request.user.is_authenticated:
        return redirect("home")
    return render(request, "core/login.html")


@login_required
def profile(request):
    """User profile view showing GitHub connection status."""
    user = request.user

    # Check if the user has a GitHub connection
    github_connected = False
    github_username = None
    social_auth = None

    try:
        # Try to get the GitHub social auth
        social_auth = UserSocialAuth.objects.filter(
            user=user, provider="github"
        ).first()

        if social_auth:
            github_connected = True

        # Get or create user profile
        profile = user.profile
        if profile.github_username:
            github_username = profile.github_username
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)

    # Handle profile update form submission
    if request.method == "POST":
        # Track if any changes were made
        changes_made = False

        # Update user information
        if user.first_name != request.POST.get("first_name", user.first_name):
            user.first_name = request.POST.get("first_name", user.first_name)
            changes_made = True

        if user.last_name != request.POST.get("last_name", user.last_name):
            user.last_name = request.POST.get("last_name", user.last_name)
            changes_made = True

        # Handle username change
        new_username = request.POST.get("username")
        if new_username and new_username != user.username:
            # Check if username is already taken
            if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                messages.error(request, "That username is already taken.")
            else:
                user.username = new_username
                messages.success(request, "Username updated successfully.")
                changes_made = True

        email = request.POST.get("email")
        if email and email != user.email:
            user.email = email
            changes_made = True

        # Update profile information
        if profile.bio != request.POST.get("bio", profile.bio):
            profile.bio = request.POST.get("bio", profile.bio)
            changes_made = True

        phone_number = request.POST.get("phone_number")
        if phone_number and phone_number != profile.phone_number:
            profile.phone_number = phone_number
            changes_made = True
            
        # Handle timezone change
        timezone = request.POST.get("timezone")
        if timezone and timezone != profile.timezone:
            # Validate timezone
            if timezone in pytz.common_timezones:
                profile.timezone = timezone
                changes_made = True

        # Save changes
        user.save()
        profile.save()

        # Show success message if changes were made (and not already shown for username)
        if changes_made and not messages.get_messages(request):
            messages.success(request, "Profile updated successfully.")

        # Redirect to avoid form resubmission
        return redirect("profile")

    # Get common timezones for the dropdown
    timezones = pytz.common_timezones

    return render(
        request,
        "core/profile.html",
        {
            "user": user,
            "profile": profile,
            "github_connected": github_connected,
            "github_username": github_username,
            "social_auth": social_auth,
            "timezones": timezones,
        },
    )


@login_required
def disconnect_github(request):
    """Disconnect GitHub from user account."""
    if request.method == "POST":
        # Find the GitHub association
        try:
            social_auth = UserSocialAuth.objects.filter(
                user=request.user, provider="github"
            ).first()
            if social_auth:
                # Clear GitHub info from profile
                profile = request.user.profile
                profile.github_username = None
                profile.github_access_token = None
                profile.save()

                # Delete the social auth
                social_auth.delete()

                messages.success(request, "GitHub account disconnected successfully.")
            else:
                messages.info(request, "No GitHub account connected.")
        except Exception as e:
            messages.error(request, f"Error disconnecting GitHub: {str(e)}")

    return redirect("profile")


async def async_github_profile(request):
    """Fetch GitHub profile data asynchronously."""

    def get_profile_and_token():
        user = request.user
        if not user.is_authenticated:
            return None, None, "Authentication required"
        try:
            profile = UserProfile.objects.get(user=user)
            if not profile.github_access_token:
                return None, None, "No GitHub token found"
            return user, profile, None
        except UserProfile.DoesNotExist:
            return None, None, "Profile does not exist"

    user, profile, error = await sync_to_async(get_profile_and_token)()
    if error:
        return HttpResponse(
            json.dumps({"error": error}), content_type="application/json"
        )

    # Now do the async HTTP call
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"token {profile.github_access_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        response = await client.get("https://api.github.com/user", headers=headers)
        if response.status_code == 200:
            return HttpResponse(response.text, content_type="application/json")
        else:
            return HttpResponse(
                json.dumps({"error": f"GitHub API error: {response.status_code}"}),
                content_type="application/json",
            )


@login_required
def logout_view(request):
    """
    Custom logout view that handles both GET and POST requests.
    Shows a confirmation page on GET and logs out on POST.
    """
    if request.method == "POST":
        auth_logout(request)
        messages.success(request, "You have been successfully logged out.")
        return redirect("login")
    return render(request, "core/logout.html")


# Add new async profile update view for use with async API
# Update profile view for use with AJAX
@login_required
@require_http_methods(["POST"])
def update_profile_ajax(request):
    """AJAX view for updating user profile."""
    try:
        # Get the user and profile
        user = request.user
        profile = user.profile

        # Parse JSON data from request
        data = json.loads(request.body)

        # Track if any changes were made
        changes_made = False

        # Update user information
        if "first_name" in data and data["first_name"] != user.first_name:
            user.first_name = data["first_name"]
            changes_made = True

        if "last_name" in data and data["last_name"] != user.last_name:
            user.last_name = data["last_name"]
            changes_made = True

        # Handle username change
        if "username" in data and data["username"] != user.username:
            # Check if username is already taken
            username_exists = (
                User.objects.filter(username=data["username"])
                .exclude(id=user.id)
                .exists()
            )
            if username_exists:
                return JsonResponse(
                    {"status": "error", "message": "That username is already taken"},
                    status=400,
                )
            user.username = data["username"]
            changes_made = True

        if "email" in data and data["email"] != user.email:
            user.email = data["email"]
            changes_made = True

        # Update profile information
        if "bio" in data and data["bio"] != profile.bio:
            profile.bio = data["bio"]
            changes_made = True

        if "phone_number" in data and data["phone_number"] != profile.phone_number:
            profile.phone_number = data["phone_number"]
            changes_made = True
            
        # Handle timezone change
        if "timezone" in data and data["timezone"] != profile.timezone:
            # Validate timezone
            if data["timezone"] in pytz.common_timezones:
                profile.timezone = data["timezone"]
                changes_made = True

        # Only save if changes were made
        if changes_made:
            # Save changes
            user.save()
            profile.save()

            # Return success with a message about what was updated
            return JsonResponse(
                {"status": "success", "message": "Profile updated successfully"}
            )
        else:
            # No changes were made
            return JsonResponse(
                {"status": "info", "message": "No changes were made to your profile"}
            )

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


# Calendar Views
@login_required
def calendar_events(request):
    """
    Return calendar events as JSON for FullCalendar.
    Optional query parameters:
    - start: Start date (YYYY-MM-DD)
    - end: End date (YYYY-MM-DD)
    """
    start_date = request.GET.get("start")
    end_date = request.GET.get("end")

    # Default to showing events for the next 30 days if no date range provided
    if not start_date:
        start_date = timezone.now().date()
    else:
        start_date = datetime.fromisoformat(start_date).date()

    if not end_date:
        end_date = start_date + timedelta(days=30)
    else:
        end_date = datetime.fromisoformat(end_date).date()

    # Convert dates to datetime objects for filtering
    start_datetime = timezone.make_aware(
        datetime.combine(start_date, datetime.min.time())
    )
    end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

    # Get events for the user within the date range
    events = CalendarEvent.objects.filter(
        user=request.user, dtstart__lte=end_datetime, dtend__gte=start_datetime
    ) | CalendarEvent.objects.filter(
        user=request.user, dtstart__range=(start_datetime, end_datetime)
    )

    # Convert to FullCalendar format
    event_data = [event.to_dict() for event in events]

    return JsonResponse(event_data, safe=False)


@login_required
@require_http_methods(["POST"])
def upload_ics(request):
    """
    Handle ICS file upload and import events.
    """
    if "ics_file" not in request.FILES:
        return JsonResponse(
            {"status": "error", "message": "No ICS file provided"}, status=400
        )

    ics_file = request.FILES["ics_file"]
    source = request.POST.get("source", "custom")

    try:
        # Read the file into memory
        file_content = io.BytesIO(ics_file.read())

        # Import events from the file
        events_created = CalendarEvent.from_ics(
            file_content, source=source, user=request.user
        )

        return JsonResponse(
            {
                "status": "success",
                "message": f"Successfully imported {events_created} events",
                "events_created": events_created,
            }
        )
    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": f"Error importing ICS file: {str(e)}"},
            status=500,
        )


@login_required
def wizard_view(request):
    """
    View for the Canvas Group to Core Team Sync Wizard.
    Renders a multi-step wizard interface for synchronizing Canvas Groups to Core Teams.
    
    Initial implementation is a mock-up without backend functionality.
    """
    # Initialize wizard session if not exists
    if 'wizard_data' not in request.session:
        request.session['wizard_data'] = {
            'current_step': 1,
            'course_id': None,
            'sync_memberships': True,
            'sync_leaders': False,
            'group_set_ids': [],
            'group_ids': [],
            'create_github_repo': False,
            'setup_project_management': False,
            'repo_pattern': '{course_code}-{group_name}',
            'confirmed': False
        }
    
    # Get the current step from the session, default to 1
    wizard_data = request.session['wizard_data']
    current_step = wizard_data.get('current_step', 1)
    
    # Process form submission if this is a POST request
    if request.method == 'POST':
        action = request.POST.get('action', '')
        
        # Update wizard data based on form submission
        if current_step == 1:
            if 'course_id' in request.POST:
                wizard_data['course_id'] = request.POST.get('course_id')
            if 'sync_memberships' in request.POST:
                wizard_data['sync_memberships'] = True
            else:
                wizard_data['sync_memberships'] = False
            if 'sync_leaders' in request.POST:
                wizard_data['sync_leaders'] = True
            else:
                wizard_data['sync_leaders'] = False
                
        elif current_step == 2:
            group_set_ids = request.POST.getlist('group_set_ids')
            wizard_data['group_set_ids'] = group_set_ids
            
        elif current_step == 3:
            group_ids = request.POST.getlist('group_ids')
            wizard_data['group_ids'] = group_ids
            
        elif current_step == 4:
            if 'create_github_repo' in request.POST:
                wizard_data['create_github_repo'] = True
            else:
                wizard_data['create_github_repo'] = False
            if 'setup_project_management' in request.POST:
                wizard_data['setup_project_management'] = True
            else:
                wizard_data['setup_project_management'] = False
            if 'repo_pattern' in request.POST:
                wizard_data['repo_pattern'] = request.POST.get('repo_pattern')
                
        elif current_step == 5:
            if 'confirmed' in request.POST:
                wizard_data['confirmed'] = True
        
        # Handle navigation between steps
        if action == 'next':
            current_step += 1
        elif action == 'previous':
            current_step -= 1
        elif action == 'finish':
            # Process the final submission
            # In a real implementation, this would create the teams
            # For now, just mark it as completed
            wizard_data['completed'] = True
            
            # Redirect to the results page
            current_step = 6
        
        # Ensure step is within valid range
        if current_step < 1:
            current_step = 1
        elif current_step > 6:
            current_step = 6
            
        # Update session
        wizard_data['current_step'] = current_step
        request.session['wizard_data'] = wizard_data
        request.session.modified = True
        
        # For AJAX requests, return JSON
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'current_step': current_step,
                'redirect': None
            })
    
    # Context data for the template
    context = {
        'progress_labels': [
            'Course Selection', 'Group Set Selection',
            'Group Selection', 'Integration Config',
            'Confirmation', 'Results'
        ],
        'current_step': current_step,
        'back_enabled': current_step > 1,
        'next_enabled': True,
        'wizard_data': wizard_data
    }
    
    # Add step-specific data
    if current_step == 1:
        context['step_data'] = {
            'courses': [
                {'id': 1, 'code': 'CS101', 'name': 'Introduction to Computer Science'},
                {'id': 2, 'code': 'MATH202', 'name': 'Advanced Calculus'},
                {'id': 3, 'code': 'ENG105', 'name': 'Academic Writing'},
            ]
        }
    elif current_step == 2:
        context['step_data'] = {
            'group_sets': [
                {'id': 1, 'name': 'Project Teams', 'group_count': 12},
                {'id': 2, 'name': 'Study Groups', 'group_count': 8},
                {'id': 3, 'name': 'Lab Partners', 'group_count': 20},
            ]
        }
    elif current_step == 3:
        # In a real implementation, this would fetch groups from the selected group sets
        context['step_data'] = {
            'groups': [
                {'id': 1, 'name': 'Team 1', 'member_count': 4, 'group_set_id': 1},
                {'id': 2, 'name': 'Team 2', 'member_count': 4, 'group_set_id': 1},
                {'id': 3, 'name': 'Team 3', 'member_count': 4, 'group_set_id': 1},
            ]
        }
    
    # Render the appropriate template
    return render(request, 'wizard/wizard_main.html', context)
