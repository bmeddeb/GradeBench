from social_core.pipeline.partial import partial
from core.models import UserProfile, Student
from django.contrib.auth.models import Group, User
import logging

logger = logging.getLogger(__name__)


def username_from_email(strategy, details, backend, user=None, *args, **kwargs):
    """
    Set username to email during user creation with social auth.
    This should be placed before create_user in the pipeline.
    """
    if user:
        return {'is_new': False}  # Skip if user already exists
    
    email = details.get('email')
    if not email:
        # GitHub requires a verified email to get the email
        return None
    
    # Use email as username
    details['username'] = email
    
    return {'username': email, 'details': details}


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
                logger.info(
                    f"Saved GitHub username {profile.github_username} for user {user.username}")

            # Save GitHub avatar URL if available
            if response.get('avatar_url'):
                profile.github_avatar_url = response.get('avatar_url')
                logger.info(
                    f"Saved GitHub avatar URL for user {user.username}")

            # Save access token if available
            if 'social' in kwargs and hasattr(kwargs['social'], 'extra_data') and 'access_token' in kwargs['social'].extra_data:
                profile.github_access_token = kwargs['social'].extra_data['access_token']
                logger.info(
                    f"Saved GitHub access token for user {user.username}")

            # Save the profile
            profile.save()
            logger.info(f"User profile saved for {user.username}")

            # If the user is a student (default for new users), add to student group
            if Group.objects.filter(name="Students").exists() and not user.groups.all().exists():
                student_group = Group.objects.get(name="Students")
                user.groups.add(student_group)
                logger.info(f"Added {user.username} to Students group")
                
                # Check if we need to create a Student record
                if not Student.objects.filter(email=user.email).exists():
                    # Create a new Student record
                    student = Student.objects.create(
                        first_name=user.first_name,
                        last_name=user.last_name,
                        email=user.email,
                        github_username=profile.github_username,
                        created_by=user
                    )
                    logger.info(f"Created Student record for {user.username}")

            return {'user': user, 'profile': profile}
        except Exception as e:
            logger.error(f"Error saving user profile: {str(e)}")
            return None
    return None