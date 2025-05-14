from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from social_django.models import UserSocialAuth
from core.models import UserProfile
import json
import httpx
from asgiref.sync import sync_to_async


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

                messages.success(
                    request, "GitHub account disconnected successfully.")
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
                json.dumps(
                    {"error": f"GitHub API error: {response.status_code}"}),
                content_type="application/json",
            )
