from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User, Group
from .models import (
    BaseUserProfile, ProfessorProfile, TAProfile, StudentProfile,
    Team, Repository, set_as_professor, set_as_ta, set_as_student
)


@login_required
def profile_view(request):
    """View for displaying and editing the user's profile"""
    user = request.user
    
    # Get the user profile type
    is_professor = hasattr(user.user_profile, 'professor_profile') if hasattr(user, 'user_profile') else False
    is_ta = hasattr(user.user_profile, 'ta_profile') if hasattr(user, 'user_profile') else False
    is_student = hasattr(user.user_profile, 'student_profile') if hasattr(user, 'user_profile') else False
    
    # Get team information if the user is a student
    team = None
    repositories = []
    if is_student:
        team = user.user_profile.student_profile.team
        if team:
            repositories = Repository.objects.filter(team=team)
    
    context = {
        'user': user,
        'is_professor': is_professor,
        'is_ta': is_ta,
        'is_student': is_student,
        'team': team,
        'repositories': repositories,
    }
    
    return render(request, 'users/profile.html', context)


@login_required
def teams_view(request):
    """View for displaying all teams"""
    user = request.user
    
    # Only professors and TAs can view all teams
    is_professor = hasattr(user.user_profile, 'professor_profile') if hasattr(user, 'user_profile') else False
    is_ta = hasattr(user.user_profile, 'ta_profile') if hasattr(user, 'user_profile') else False
    
    if not (is_professor or is_ta):
        messages.error(request, "You don't have permission to view all teams.")
        return redirect('profile')
    
    teams = Team.objects.all()
    
    context = {
        'teams': teams,
    }
    
    return render(request, 'users/teams.html', context)


@login_required
def team_detail_view(request, team_id):
    """View for displaying team details"""
    user = request.user
    team = get_object_or_404(Team, id=team_id)
    
    # Check if the user has permission to view this team
    is_professor = hasattr(user.user_profile, 'professor_profile') if hasattr(user, 'user_profile') else False
    is_ta = hasattr(user.user_profile, 'ta_profile') if hasattr(user, 'user_profile') else False
    is_team_member = (hasattr(user.user_profile, 'student_profile') and 
                      user.user_profile.student_profile.team == team) if hasattr(user, 'user_profile') else False
    
    if not (is_professor or is_ta or is_team_member):
        messages.error(request, "You don't have permission to view this team.")
        return redirect('profile')
    
    # Get team members and repositories
    members = StudentProfile.objects.filter(team=team)
    repositories = Repository.objects.filter(team=team)
    
    context = {
        'team': team,
        'members': members,
        'repositories': repositories,
    }
    
    return render(request, 'users/team_detail.html', context)


@login_required
def create_team_view(request):
    """View for creating a new team"""
    user = request.user
    
    # Only professors can create teams
    is_professor = hasattr(user.user_profile, 'professor_profile') if hasattr(user, 'user_profile') else False
    
    if not is_professor:
        messages.error(request, "You don't have permission to create teams.")
        return redirect('profile')
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        github_org = request.POST.get('github_org')
        
        if name:
            team = Team.objects.create(
                name=name,
                description=description,
                github_organization=github_org
            )
            messages.success(request, f"Team {team.name} created successfully.")
            return redirect('team_detail', team_id=team.id)
        else:
            messages.error(request, "Team name is required.")
    
    return render(request, 'users/create_team.html')


@login_required
def add_student_to_team_view(request, team_id):
    """View for adding a student to a team"""
    user = request.user
    team = get_object_or_404(Team, id=team_id)
    
    # Only professors and TAs can add students to teams
    is_professor = hasattr(user.user_profile, 'professor_profile') if hasattr(user, 'user_profile') else False
    is_ta = hasattr(user.user_profile, 'ta_profile') if hasattr(user, 'user_profile') else False
    
    if not (is_professor or is_ta):
        messages.error(request, "You don't have permission to add students to teams.")
        return redirect('team_detail', team_id=team.id)
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        
        if student_id:
            try:
                student = User.objects.get(id=student_id)
                student_profile = StudentProfile.objects.get(user_profile__user=student)
                student_profile.team = team
                student_profile.save()
                messages.success(request, f"{student.get_full_name()} added to team {team.name}.")
            except User.DoesNotExist:
                messages.error(request, "Student not found.")
            except StudentProfile.DoesNotExist:
                messages.error(request, "Student profile not found.")
        else:
            messages.error(request, "Student is required.")
    
    # Get all students not in a team
    available_students = StudentProfile.objects.filter(team__isnull=True)
    
    context = {
        'team': team,
        'available_students': available_students,
    }
    
    return render(request, 'users/add_student_to_team.html', context)


@login_required
def add_repository_view(request, team_id):
    """View for adding a repository to a team"""
    user = request.user
    team = get_object_or_404(Team, id=team_id)
    
    # Only professors, TAs, and team members can add repositories
    is_professor = hasattr(user.user_profile, 'professor_profile') if hasattr(user, 'user_profile') else False
    is_ta = hasattr(user.user_profile, 'ta_profile') if hasattr(user, 'user_profile') else False
    is_team_member = (hasattr(user.user_profile, 'student_profile') and 
                      user.user_profile.student_profile.team == team) if hasattr(user, 'user_profile') else False
    
    if not (is_professor or is_ta or is_team_member):
        messages.error(request, "You don't have permission to add repositories to this team.")
        return redirect('team_detail', team_id=team.id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        github_repo_id = request.POST.get('github_repo_id')
        github_full_name = request.POST.get('github_full_name')
        github_clone_url = request.POST.get('github_clone_url')
        description = request.POST.get('description')
        
        if name and github_repo_id and github_full_name and github_clone_url:
            repository = Repository.objects.create(
                name=name,
                github_repo_id=github_repo_id,
                github_full_name=github_full_name,
                github_clone_url=github_clone_url,
                description=description,
                team=team
            )
            messages.success(request, f"Repository {repository.name} added successfully.")
            return redirect('team_detail', team_id=team.id)
        else:
            messages.error(request, "All required fields must be provided.")
    
    context = {
        'team': team,
    }
    
    return render(request, 'users/add_repository.html', context)


@login_required
def manage_user_roles_view(request):
    """View for managing user roles (professor, TA, student)"""
    user = request.user
    
    # Only professors can manage user roles
    is_professor = hasattr(user.user_profile, 'professor_profile') if hasattr(user, 'user_profile') else False
    
    if not is_professor:
        messages.error(request, "You don't have permission to manage user roles.")
        return redirect('profile')
    
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        role = request.POST.get('role')
        
        if user_id and role:
            try:
                target_user = User.objects.get(id=user_id)
                
                if role == 'professor':
                    set_as_professor(target_user)
                    messages.success(request, f"{target_user.get_full_name()} is now a professor.")
                elif role == 'ta':
                    set_as_ta(target_user)
                    messages.success(request, f"{target_user.get_full_name()} is now a TA.")
                elif role == 'student':
                    set_as_student(target_user)
                    messages.success(request, f"{target_user.get_full_name()} is now a student.")
                else:
                    messages.error(request, "Invalid role.")
            except User.DoesNotExist:
                messages.error(request, "User not found.")
        else:
            messages.error(request, "User and role are required.")
    
    # Get all users
    users = User.objects.all()
    
    # Get user roles
    user_roles = []
    for u in users:
        role = 'Other'
        if u.groups.filter(name='Professors').exists():
            role = 'Professor'
        elif u.groups.filter(name='TAs').exists():
            role = 'TA'
        elif u.groups.filter(name='Students').exists():
            role = 'Student'
        
        user_roles.append({
            'user': u,
            'role': role
        })
    
    context = {
        'user_roles': user_roles,
    }
    
    return render(request, 'users/manage_user_roles.html', context)
