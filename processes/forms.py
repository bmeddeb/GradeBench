from django import forms
from django.utils.translation import gettext_lazy as _
from lms.canvas.models import CanvasCourse, CanvasGroupCategory, CanvasGroup
from django_select2.forms import Select2Widget, Select2MultipleWidget


class TeamWizardStep1Form(forms.Form):
    """Step 1: Course Selection Form - Select from Canvas courses linked to teams"""
    course = forms.ModelChoiceField(
        queryset=CanvasCourse.objects.filter(teams__isnull=False).distinct(),
        label=_('Select Canvas Course'),
        widget=Select2Widget(attrs={
            'class': 'form-select select2',
            'data-placeholder': 'Select a Canvas course with teams',
            'data-theme': 'bootstrap-5'
        }),
        help_text=_('Only courses with existing teams are shown')
    )
    use_github = forms.BooleanField(
        required=False,
        label=_('GitHub'),
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        })
    )
    use_taiga = forms.BooleanField(
        required=False,
        label=_('Taiga'),
        initial=True,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input',
            'role': 'switch'
        })
    )


class TeamWizardStep2Form(forms.Form):
    """Step 2: Team Selection Form"""
    teams = forms.ModelMultipleChoiceField(
        queryset=None,  # Will be set dynamically
        label=_('Select Teams to Update'),
        widget=forms.MultipleHiddenInput(),
        required=True
    )

    def __init__(self, *args, **kwargs):
        course_id = kwargs.pop('course_id', None)
        super().__init__(*args, **kwargs)
        
        print(f"TeamWizardStep2Form init with course_id={course_id}")

        if course_id:
            from core.models import Team
            # Debug: Check if teams exist for this course
            teams_query = Team.objects.filter(
                canvas_course_id=course_id
            ).order_by('name')
            print(f"Found {teams_query.count()} teams for course_id={course_id}")
            
            self.fields['teams'].queryset = teams_query
            
            # Store teams for template display
            self.teams_list = list(self.fields['teams'].queryset)
            print(f"Teams list contains {len(self.teams_list)} teams")


class TeamWizardStep3Form(forms.Form):
    """Step 3: GitHub Configuration Form"""
    # Dynamic form - fields will be created in __init__

    def __init__(self, *args, **kwargs):
        # Get selected teams from previous steps
        selected_teams = kwargs.pop('selected_teams', [])
        super().__init__(*args, **kwargs)
        
        from core.models import Team, Student
        from lms.canvas.models import CanvasCourse
        import re

        # Create dynamic fields for each team
        for team in selected_teams:
            # Get course code for repo name template
            course_code = ""
            if team.canvas_course:
                course_code = team.canvas_course.course_code
                # Clean the course code
                course_code = re.sub(r'[^\w\-]', '-', course_code).strip('-')
            
            # Get Canvas group name if available
            group_name = team.name
            # Clean the group name
            clean_group_name = re.sub(r'[^\w\-]', '-', group_name).strip('-')
            
            # Generate default repo name
            default_repo_name = f"{course_code}-{clean_group_name}".lower()
            
            # Add GitHub organization field (team leader username)
            org_field_name = f'github_organization_{team.id}'
            self.fields[org_field_name] = forms.CharField(
                max_length=100,
                required=False,
                label=f'GitHub Organization for {team.name}',
                help_text='Team leader username: first letter of firstname + lastname',
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': 'e.g., jdoe'
                })
            )
            
            # Add GitHub repository name field
            repo_field_name = f'github_repo_name_{team.id}'
            self.fields[repo_field_name] = forms.CharField(
                max_length=100,
                required=False,
                label=f'GitHub Repository for {team.name}',
                initial=default_repo_name,
                help_text=f'Template: {course_code}-{clean_group_name}',
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': f'e.g., {default_repo_name}'
                })
            )
            
            # Calculate team leader username suggestion
            students = Student.objects.filter(team=team).order_by('first_name', 'last_name')
            
            if students.exists():
                leader = students.first()
                
                # Ensure we have valid names
                if leader.first_name and leader.last_name:
                    # Remove ALL special characters and spaces from names
                    # Keep only alphanumeric characters
                    first_name = re.sub(r'[^a-zA-Z0-9]', '', leader.first_name).strip()
                    last_name = re.sub(r'[^a-zA-Z0-9]', '', leader.last_name).strip()
                    
                    if first_name and last_name:
                        # Create username: first letter of first name + full last name
                        username = f"{first_name[0].lower()}{last_name.lower()}"
                        
                        # Pre-fill the organization field with the calculated username
                        self.initial[org_field_name] = username
                        self.fields[org_field_name].help_text = f'Suggested: {username} (from {leader.full_name})'
                    else:
                        # If names are empty after cleaning, just use the original names
                        # with basic cleaning (lowercase, no spaces)
                        fallback_first = leader.first_name.replace(' ', '').lower() if leader.first_name else ''
                        fallback_last = leader.last_name.replace(' ', '').lower() if leader.last_name else ''
                        if fallback_first and fallback_last:
                            username = f"{fallback_first[0]}{fallback_last}"
                            self.initial[org_field_name] = username
                            self.fields[org_field_name].help_text = f'Suggested: {username} (from {leader.full_name})'


class TeamWizardStep4Form(forms.Form):
    """Step 4: Taiga Configuration Form"""
    # Dynamic form - fields will be created in __init__

    def __init__(self, *args, **kwargs):
        # Get selected teams from previous steps
        selected_teams = kwargs.pop('selected_teams', [])
        super().__init__(*args, **kwargs)
        
        from core.models import Team
        import re

        # Create dynamic fields for each team
        for team in selected_teams:
            # Get course code for project name template
            course_code = ""
            if team.canvas_course:
                course_code = team.canvas_course.course_code
                # Clean the course code
                course_code = re.sub(r'[^\w\-]', '-', course_code).strip('-')
            
            # Get Canvas group name if available
            group_name = team.name
            # Clean the group name
            clean_group_name = re.sub(r'[^\w\-]', '-', group_name).strip('-')
            
            # Generate default project name
            default_project_name = f"{course_code}-{clean_group_name}".lower()
            
            # Add Taiga project name field
            project_field_name = f'taiga_project_{team.id}'
            self.fields[project_field_name] = forms.CharField(
                max_length=100,
                required=False,
                label=f'Taiga Project for {team.name}',
                initial=default_project_name,
                help_text=f'Template: {course_code}-{clean_group_name}',
                widget=forms.TextInput(attrs={
                    'class': 'form-control',
                    'placeholder': f'e.g., {default_project_name}'
                })
            )


class TeamWizardStep5Form(forms.Form):
    """Step 5: Confirmation Form"""
    confirm = forms.BooleanField(
        required=True,
        label=_('I confirm that I want to update the selected teams'),
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
