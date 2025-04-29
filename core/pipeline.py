from social_core.pipeline.partial import partial
from core.models import UserProfile
from django.contrib.auth.models import Group
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
            # Get or create the legacy user profile (for backward compatibility)
            profile, created = UserProfile.objects.get_or_create(user=user)
            
            # Save GitHub username if available
            if response.get('login'):
                profile.github_username = response.get('login')
                logger.info(f"Saved GitHub username {profile.github_username} for user {user.username}")
            
            # Save GitHub avatar URL if available
            if response.get('avatar_url'):
                profile.github_avatar_url = response.get('avatar_url')
                logger.info(f"Saved GitHub avatar URL for user {user.username}")
            
            # Save access token if available
            if 'social' in kwargs and hasattr(kwargs['social'], 'extra_data') and 'access_token' in kwargs['social'].extra_data:
                profile.github_access_token = kwargs['social'].extra_data['access_token']
                logger.info(f"Saved GitHub access token for user {user.username}")
            
            # Save the profile
            profile.save()
            logger.info(f"Legacy user profile saved for {user.username}")
            
            # Also try to save to the new user profile system if it's available
            try:
                from users.models import BaseUserProfile, StudentProfile
                
                # Get or create the base user profile
                base_profile, created = BaseUserProfile.objects.get_or_create(user=user)
                
                # If the user is a student (default for new users), update their GitHub info
                if Group.objects.filter(name="Students").exists() and not user.groups.all().exists():
                    student_group = Group.objects.get(name="Students")
                    user.groups.add(student_group)
                
                if user.groups.filter(name="Students").exists() and hasattr(base_profile, 'student_profile'):
                    student_profile = base_profile.student_profile
                    student_profile.github_username = profile.github_username
                    student_profile.save()
                    logger.info(f"Updated student profile GitHub info for {user.username}")
                elif user.groups.filter(name="Students").exists():
                    # Create a student profile
                    from users.models import set_as_student
                    set_as_student(user, github_username=profile.github_username)
                    logger.info(f"Created student profile for {user.username}")
                
                logger.info(f"New user profile system updated for {user.username}")
            except (ImportError, ModuleNotFoundError):
                # New user profile system not available, skip
                logger.warning("New users app not available, skipping new profile update")
            
            return {'user': user, 'profile': profile}
        except Exception as e:
            logger.error(f"Error saving user profile: {str(e)}")
            return None
    return None
