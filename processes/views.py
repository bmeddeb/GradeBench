from django.shortcuts import render, redirect
from django.views.generic import ListView
from django.contrib import messages
from django.urls import reverse
from formtools.wizard.views import SessionWizardView
from django.db import transaction

from .models import Process
from .forms import (
    TeamWizardStep1Form,
    TeamWizardStep2Form,
    TeamWizardStep3Form,
    TeamWizardStep4Form,
    TeamWizardStep5Form,
)

# Create your views here.


class ProcessListView(ListView):
    """View to list all processes."""
    model = Process
    template_name = 'processes/process_list.html'
    context_object_name = 'processes'
    paginate_by = 10


class TeamWizard(SessionWizardView):
    """
    Multi-step wizard for updating Teams with GitHub and Taiga integrations.

    Steps:
    1. Course Selection (with GitHub and Taiga toggles)
    2. Team Selection
    3. GitHub Configuration (conditional)
    4. Taiga Configuration (conditional)
    5. Confirmation & Update
    """
    form_list = [
        ('course_selection', TeamWizardStep1Form),
        ('team_selection', TeamWizardStep2Form),
        ('github_config', TeamWizardStep3Form),
        ('taiga_config', TeamWizardStep4Form),
        ('confirmation', TeamWizardStep5Form),
    ]
    template_name = 'processes/team_wizard.html'
    
    def get(self, request, *args, **kwargs):
        """Handle the reset parameter to clear wizard data"""
        if request.GET.get('reset') == '1':
            # Reset the storage before processing
            try:
                self.storage.reset()
            except:
                # If storage doesn't exist yet, that's fine
                pass
            # Redirect to the same URL without the reset parameter
            return redirect('processes:team_wizard')
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self, step=None):
        """Pass dynamic parameters to forms based on previous steps."""
        kwargs = super().get_form_kwargs(step)

        if step == 'team_selection':
            # Pass course_id from step 1 to step 2
            step1_data = self.get_cleaned_data_for_step('course_selection')
            if step1_data:
                kwargs['course_id'] = step1_data.get(
                    'course').id if step1_data.get('course') else None
                print(
                    f"Passing course_id={kwargs['course_id']} to team_selection form")

        elif step == 'github_config' or step == 'taiga_config':
            # Pass selected teams to GitHub or Taiga configuration form
            step2_data = self.get_cleaned_data_for_step('team_selection')

            if step2_data:
                selected_teams = step2_data.get('teams', [])
                kwargs['selected_teams'] = selected_teams
                print(
                    f"Passing {len(selected_teams)} selected teams to {step} form")
            else:
                print(f"Missing data for {step} form")

        return kwargs

    def get_template_names(self):
        """Return specific template for steps if they exist."""
        return [
            f'processes/team_wizard_{self.steps.current}.html',
            self.template_name,
        ]

    def get_context_data(self, form, **kwargs):
        """Add extra context for each step."""
        context = super().get_context_data(form, **kwargs)

        # Add step-specific context
        if self.steps.current == 'confirmation':
            # Get data from previous steps
            step1_data = self.get_cleaned_data_for_step(
                'course_selection') or {}
            step2_data = self.get_cleaned_data_for_step(
                'team_selection') or {}

            # Get GitHub and Taiga data if those steps were used
            github_data = {}
            taiga_data = {}

            if self.condition_github_config():
                github_data = self.get_cleaned_data_for_step(
                    'github_config') or {}

            if self.condition_taiga_config():
                taiga_data = self.get_cleaned_data_for_step(
                    'taiga_config') or {}

            # Get selected teams info
            from core.models import Team
            selected_teams = step2_data.get('teams', [])
            teams_summary = []

            if selected_teams:
                for team in selected_teams:
                    team_info = {
                        'id': team.id,
                        'name': team.name,
                        'description': team.description,
                    }

                    # Add GitHub data if GitHub is enabled
                    if step1_data.get('use_github'):
                        org_field_name = f'github_organization_{team.id}'
                        repo_field_name = f'github_repo_name_{team.id}'
                        team_info['github_organization'] = github_data.get(
                            org_field_name, '')
                        team_info['github_repo_name'] = github_data.get(
                            repo_field_name, '')

                    # Add Taiga project name if Taiga is enabled
                    if step1_data.get('use_taiga'):
                        project_field_name = f'taiga_project_{team.id}'
                        team_info['taiga_project'] = taiga_data.get(
                            project_field_name, '')

                    teams_summary.append(team_info)

            # Pass summary data to template
            context['teams_summary'] = teams_summary
            context['course_name'] = step1_data.get(
                'course').name if step1_data.get('course') else "Unknown Course"
            context['use_github'] = step1_data.get('use_github', False)
            context['use_taiga'] = step1_data.get('use_taiga', False)

        # Pass teams_list from Step 2 form
        elif self.steps.current == 'team_selection' and hasattr(form, 'teams_list'):
            context['teams_list'] = form.teams_list

        # Add step titles for display in the template
        context['step_titles'] = {
            'course_selection': 'Course Selection',
            'team_selection': 'Team Selection',
            'github_config': 'GitHub Config',
            'taiga_config': 'Taiga Config',
            'confirmation': 'Confirmation',
        }

        # Add more compact step titles for the progress indicators
        context['step_short_titles'] = {
            'course_selection': 'Course',
            'team_selection': 'Teams',
            'github_config': 'GitHub',
            'taiga_config': 'Taiga',
            'confirmation': 'Confirm',
        }

        return context

    def condition_github_config(self):
        """Only show GitHub config step if use_github was checked in step 1."""
        step1_data = self.get_cleaned_data_for_step('course_selection')
        return step1_data and step1_data.get('use_github', False)

    def condition_taiga_config(self):
        """Only show Taiga config step if use_taiga was checked in step 1."""
        step1_data = self.get_cleaned_data_for_step('course_selection')
        return step1_data and step1_data.get('use_taiga', False)

    def done(self, form_list, **kwargs):
        """Process the wizard data and update Teams with GitHub/Taiga info."""
        # Get the data from each step
        step1_data = self.get_cleaned_data_for_step('course_selection')
        step2_data = self.get_cleaned_data_for_step('team_selection')

        github_data = {}
        if self.condition_github_config():
            github_data = self.get_cleaned_data_for_step('github_config') or {}

        taiga_data = {}
        if self.condition_taiga_config():
            taiga_data = self.get_cleaned_data_for_step('taiga_config') or {}

        # Get selected teams
        selected_teams = step2_data.get('teams', [])

        if not selected_teams:
            messages.error(
                self.request, 'No teams selected for update.')
            return redirect('processes:process_list')

        # Track statistics for final message
        updated_count = 0
        errors = []

        # Update teams with GitHub and Taiga information
        for team in selected_teams:
            try:
                # Get GitHub data if enabled
                if step1_data.get('use_github'):
                    org_field_name = f'github_organization_{team.id}'
                    repo_field_name = f'github_repo_name_{team.id}'
                    team.github_organization = github_data.get(org_field_name, '')
                    team.github_repo_name = github_data.get(repo_field_name, '')

                # Get Taiga data if enabled
                if step1_data.get('use_taiga'):
                    project_field_name = f'taiga_project_{team.id}'
                    team.taiga_project = taiga_data.get(project_field_name, '')

                # Save the team with updated information
                team.save()
                updated_count += 1
                print(f"Updated team: {team.id} - {team.name}")

            except Exception as e:
                errors.append(
                    f"Error updating team {team.name}: {str(e)}")

        # Create appropriate message
        if updated_count > 0:
            success_msg = f"Success! {updated_count} team(s) updated."
            messages.success(self.request, success_msg)
        else:
            messages.warning(self.request, "No teams were updated.")

        # Add errors if any
        if errors:
            messages.error(
                self.request, f"Errors occurred: {'; '.join(errors)}")

        # Redirect to process list
        return redirect('processes:process_list')

    def process_step(self, form):
        """Process the form for the current step."""
        # Log form data for debugging
        step_name = self.steps.current
        print(f"Processing {step_name} form")
        print(f"Form data: {form.data}")
        print(f"Form cleaned_data: {form.cleaned_data}")
        return super().process_step(form)
