from social_core.pipeline.partial import partial
from .models import UserProfile
import logging

logger = logging.getLogger(__name__)

def save_profile(backend, user, response, *args, **kwargs):
    """
    Save GitHub data to UserProfile.
    This is called when a user successfully authenticates with GitHub.
    It links the GitHub account to an existing Django user if email matches.
    """
    if backend.name == 'github':
        try:
            # Get or create the user profile
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Save GitHub username if available
            if response.get('login'):
                profile.github_username = response.get('login')
                logger.info(f"Saved GitHub username {profile.github_username} for user {user.username}")
            
            # Save access token if available
            if 'social' in kwargs and hasattr(kwargs['social'], 'extra_data') and 'access_token' in kwargs['social'].extra_data:
                profile.github_access_token = kwargs['social'].extra_data['access_token']
                logger.info(f"Saved GitHub access token for user {user.username}")
            
            # Save the profile
            profile.save()
            logger.info(f"User profile saved for {user.username}")
            
            return {'user': user, 'profile': profile}
        except Exception as e:
            logger.error(f"Error saving user profile: {str(e)}")
            return None
    return None 