from django.contrib.auth.models import User, Group
from django.db.models import Q
from django.utils import timezone
from .models import BaseUserProfile, ProfessorProfile, TAProfile, StudentProfile, Team, Repository, GitHubToken


def create_default_groups():
    """Create the default user groups if they don't exist"""
    groups = ['Professors', 'TAs', 'Students', 'Others']
    created_groups = []
    
    for group_name in groups:
        group, created = Group.objects.get_or_create(name=group_name)
        if created:
            created_groups.append(group_name)
    
    return created_groups


def get_users_by_group(group_name):
    """Get all users in a specific group"""
    try:
        group = Group.objects.get(name=group_name)
        return group.user_set.all()
    except Group.DoesNotExist:
        return User.objects.none()


def get_all_professors():
    """Get all professors"""
    return get_users_by_group('Professors')


def get_all_tas():
    """Get all TAs"""
    return get_users_by_group('TAs')


def get_all_students():
    """Get all students"""
    return get_users_by_group('Students')


def get_professor_profiles():
    """Get all professor profiles"""
    return ProfessorProfile.objects.all()


def get_ta_profiles():
    """Get all TA profiles"""
    return TAProfile.objects.all()


def get_student_profiles():
    """Get all student profiles"""
    return StudentProfile.objects.all()


def get_teams_for_professor(professor_user):
    """Get all teams that a professor has access to"""
    # For now, professors have access to all teams
    return Team.objects.all()


def get_teams_for_ta(ta_user):
    """Get all teams that a TA has access to"""
    # For now, TAs have access to all teams
    return Team.objects.all()


def get_team_members(team):
    """Get all members of a team"""
    return StudentProfile.objects.filter(team=team)


def get_available_github_token():
    """
    Get an available GitHub token that is not rate-limited
    Uses a simple round-robin selection strategy
    """
    # Get all tokens that are not rate limited
    available_tokens = GitHubToken.objects.filter(
        Q(rate_limit_remaining__gt=10) | Q(rate_limit_reset__lte=timezone.now())
    ).order_by('last_used')
    
    if available_tokens.exists():
        # Get the least recently used token
        token = available_tokens.first()
        token.last_used = timezone.now()
        token.save()
        return token
    
    return None


def update_token_rate_limit(token, remaining, reset_time):
    """Update the rate limit information for a token"""
    if isinstance(token, str):
        # If token string is provided, find the token object
        try:
            token = GitHubToken.objects.get(token=token)
        except GitHubToken.DoesNotExist:
            return False
    
    token.rate_limit_remaining = remaining
    token.rate_limit_reset = reset_time
    token.save()
    return True


def create_team(name, description=None, github_org=None, github_team_id=None, taiga_project_id=None):
    """Create a new team"""
    team = Team.objects.create(
        name=name,
        description=description,
        github_organization=github_org,
        github_team_id=github_team_id,
        taiga_project_id=taiga_project_id
    )
    return team


def add_student_to_team(student_user, team):
    """Add a student to a team"""
    try:
        student_profile = student_user.user_profile.student_profile
        student_profile.team = team
        student_profile.save()
        return True
    except StudentProfile.DoesNotExist:
        return False


def create_repository(name, description, github_repo_id, github_full_name, github_clone_url, team):
    """Create a new repository and associate it with a team"""
    repo = Repository.objects.create(
        name=name,
        description=description,
        github_repo_id=github_repo_id,
        github_full_name=github_full_name,
        github_clone_url=github_clone_url,
        team=team
    )
    return repo


def get_repositories_for_team(team):
    """Get all repositories for a team"""
    return Repository.objects.filter(team=team)


def get_repositories_for_student(student_user):
    """Get all repositories for a student based on their team"""
    try:
        student_profile = student_user.user_profile.student_profile
        if student_profile.team:
            return Repository.objects.filter(team=student_profile.team)
    except StudentProfile.DoesNotExist:
        pass
    
    return Repository.objects.none()
