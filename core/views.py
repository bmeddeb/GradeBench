from django.shortcuts import render, redirect
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.urls import reverse
from social_django.models import UserSocialAuth
from django.contrib.auth.models import User
from .models import UserProfile
import httpx
import json
from asgiref.sync import sync_to_async
from django.core.exceptions import SynchronousOnlyOperation
from core.db import async_save

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

    # Handle profile update form submission
    if request.method == 'POST':
        # Update user information
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        
        # Handle username change
        new_username = request.POST.get('username')
        if new_username and new_username != user.username:
            # Check if username is already taken
            if User.objects.filter(username=new_username).exclude(id=user.id).exists():
                messages.error(request, "That username is already taken.")
            else:
                user.username = new_username
                messages.success(request, "Username updated successfully.")
        
        email = request.POST.get('email')
        if email and email != user.email:
            user.email = email

        # Update profile information
        profile.bio = request.POST.get('bio', profile.bio)
        phone_number = request.POST.get('phone_number')
        if phone_number:
            profile.phone_number = phone_number

        # Save changes
        user.save()
        profile.save()

        # Redirect to avoid form resubmission
        return redirect('profile')

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
        auth_logout(request)
        messages.success(request, "You have been successfully logged out.")
        return redirect('login')
    return render(request, 'core/logout.html')


# Add new async profile update view for use with async API
@login_required
async def update_profile_async(request):
    """Async view for updating user profile."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Method not allowed'}, status=405)

    try:
        # Get the user and profile
        user = request.user
        profile = await sync_to_async(getattr)(user, 'profile')

        # Parse JSON data from request
        data = json.loads(request.body)

        # Update user information
        if 'first_name' in data:
            user.first_name = data['first_name']
        if 'last_name' in data:
            user.last_name = data['last_name']
        
        # Handle username change
        if 'username' in data and data['username'] != user.username:
            # Check if username is already taken
            username_exists = await sync_to_async(
                lambda: User.objects.filter(username=data['username']).exclude(id=user.id).exists()
            )()
            if username_exists:
                return JsonResponse({
                    'status': 'error', 
                    'message': 'That username is already taken'
                }, status=400)
            user.username = data['username']
            
        if 'email' in data:
            user.email = data['email']

        # Update profile information
        if 'bio' in data:
            profile.bio = data['bio']
        if 'phone_number' in data:
            profile.phone_number = data['phone_number']

        # Save changes using async helpers
        await async_save(user)
        await async_save(profile)

        return JsonResponse({'status': 'success'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
