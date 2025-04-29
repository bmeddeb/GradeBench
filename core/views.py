from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse
from django.contrib import messages
from django.urls import reverse
from social_django.models import UserSocialAuth
from .models import UserProfile
import httpx
import json
from asgiref.sync import sync_to_async
from django.core.exceptions import SynchronousOnlyOperation

# Create your views here.


@login_required
def home(request):
    """Home page view."""
    return render(request, 'core/home.html', {
        'user': request.user,
        'profile': request.user.profile,
    })


def login(request):
    """Login page view."""
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'core/login.html')


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
            user=user, provider='github').first()

        if social_auth:
            github_connected = True

        # Get or create user profile
        profile = user.profile
        if profile.github_username:
            github_username = profile.github_username
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=user)

    return render(request, 'core/profile.html', {
        'user': user,
        'profile': profile,
        'github_connected': github_connected,
        'github_username': github_username,
        'social_auth': social_auth,
    })


@login_required
def disconnect_github(request):
    """Disconnect GitHub from user account."""
    if request.method == 'POST':
        # Find the GitHub association
        try:
            social_auth = UserSocialAuth.objects.filter(
                user=request.user, provider='github').first()
            if social_auth:
                # Clear GitHub info from profile
                profile = request.user.profile
                profile.github_username = None
                profile.github_access_token = None
                profile.save()

                # Delete the social auth
                social_auth.delete()

                messages.success(
                    request, "GitHub account disconnected successfully.")
            else:
                messages.info(request, "No GitHub account connected.")
        except Exception as e:
            messages.error(request, f"Error disconnecting GitHub: {str(e)}")

    return redirect('profile')


async def async_github_profile(request):
    """Fetch GitHub profile data asynchronously."""
    def get_profile_and_token():
        user = request.user
        if not user.is_authenticated:
            return None, None, 'Authentication required'
        try:
            profile = UserProfile.objects.get(user=user)
            if not profile.github_access_token:
                return None, None, 'No GitHub token found'
            return user, profile, None
        except UserProfile.DoesNotExist:
            return None, None, 'Profile does not exist'

    user, profile, error = await sync_to_async(get_profile_and_token)()
    if error:
        return HttpResponse(json.dumps({'error': error}), content_type='application/json')

    # Now do the async HTTP call
    async with httpx.AsyncClient() as client:
        headers = {
            'Authorization': f'token {profile.github_access_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        response = await client.get('https://api.github.com/user', headers=headers)
        if response.status_code == 200:
            return HttpResponse(response.text, content_type='application/json')
        else:
            return HttpResponse(
                json.dumps(
                    {'error': f'GitHub API error: {response.status_code}'}),
                content_type='application/json'
            )


@login_required
def logout_view(request):
    """
    Custom logout view that handles both GET and POST requests.
    Shows a confirmation page on GET and logs out on POST.
    """
    if request.method == 'POST':
        from django.contrib.auth import logout
        logout(request)
        messages.success(request, "You have been successfully logged out.")
        return redirect('login')
    return render(request, 'core/logout.html')
