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
    TeamWizardStep6Form,
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
    Multi-step wizard for creating Teams from Canvas Groups.

    Steps:
    1. Course Selection (with GitHub and Taiga toggles)
    2. Group Set Selection
    3. Group Selection
    4. GitHub Configuration (conditional)
    5. Taiga Configuration (conditional)
    6. Confirmation & Persistence
    """
    form_list = [
        ('course_selection', TeamWizardStep1Form),
        ('group_set_selection', TeamWizardStep2Form),
        ('group_selection', TeamWizardStep3Form),
        ('github_config', TeamWizardStep4Form),
        ('taiga_config', TeamWizardStep5Form),
        ('confirmation', TeamWizardStep6Form),
    ]
    template_name = 'processes/team_wizard.html'

    def get_form_kwargs(self, step=None):
        """Pass dynamic parameters to forms based on previous steps."""
        kwargs = super().get_form_kwargs(step)

        if step == 'group_set_selection':
            # Pass course_id from step 1 to step 2
            step1_data = self.get_cleaned_data_for_step('course_selection')
            if step1_data:
                kwargs['course_id'] = step1_data.get(
                    'course').id if step1_data.get('course') else None
                print(
                    f"Passing course_id={kwargs['course_id']} to group_set_selection form")

        elif step == 'group_selection':
            # Pass selected group categories from step 2 to step 3
            step2_data = self.get_cleaned_data_for_step('group_set_selection')
            if step2_data:
                categories = step2_data.get('group_categories', [])
                kwargs['category_ids'] = [cat.id for cat in categories]
                print(
                    f"Passing category_ids={kwargs['category_ids']} to group_selection form")
            else:
                print("No data from step 2 - group_set_selection")

        elif step == 'github_config' or step == 'taiga_config':
            # Pass selected groups and course to GitHub or Taiga configuration form
            step1_data = self.get_cleaned_data_for_step('course_selection')
            step3_data = self.get_cleaned_data_for_step('group_selection')

            if step1_data and step3_data:
                course = step1_data.get('course')
                selected_group_ids = step3_data.get('selected_groups', [])

                kwargs['course'] = course
                kwargs['selected_group_ids'] = selected_group_ids
                print(
                    f"Passing course={course} and {len(selected_group_ids)} selected groups to {step} form")
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
            step3_data = self.get_cleaned_data_for_step(
                'group_selection') or {}

            # Get GitHub and Taiga data if those steps were used
            github_data = {}
            taiga_data = {}

            if self.condition_github_config():
                github_data = self.get_cleaned_data_for_step(
                    'github_config') or {}

            if self.condition_taiga_config():
                taiga_data = self.get_cleaned_data_for_step(
                    'taiga_config') or {}

            # Get selected groups info
            from lms.canvas.models import CanvasGroup
            selected_group_ids = step3_data.get('selected_groups', [])
            teams_summary = []

            if selected_group_ids:
                for group_id in selected_group_ids:
                    try:
                        group = CanvasGroup.objects.get(id=group_id)
                        team_info = {
                            'id': group.id,
                            'name': group.name,
                            'description': group.description,
                        }

                        # Add GitHub repo name if GitHub is enabled
                        if step1_data.get('use_github'):
                            repo_field_name = f'repo_name_{group_id}'
                            team_info['github_repo_name'] = github_data.get(
                                repo_field_name, '')

                        # Add Taiga project name if Taiga is enabled
                        if step1_data.get('use_taiga'):
                            project_field_name = f'project_name_{group_id}'
                            team_info['taiga_project'] = taiga_data.get(
                                project_field_name, '')

                        teams_summary.append(team_info)
                    except CanvasGroup.DoesNotExist:
                        continue

            # Pass summary data to template
            context['teams_summary'] = teams_summary
            context['course_name'] = step1_data.get(
                'course').name if step1_data.get('course') else "Unknown Course"
            context['use_github'] = step1_data.get('use_github', False)
            context['use_taiga'] = step1_data.get('use_taiga', False)

        # Pass groups_by_category from Step 3 form
        elif self.steps.current == 'group_selection' and hasattr(form, 'groups_by_category'):
            context['groups_by_category'] = form.groups_by_category

        # Add step titles for display in the template
        context['step_titles'] = {
            'course_selection': 'Course Selection',
            'group_set_selection': 'Group Set Selection',
            'group_selection': 'Group Selection',
            'github_config': 'GitHub Config',
            'taiga_config': 'Taiga Config',
            'confirmation': 'Confirmation',
        }

        # Add more compact step titles for the progress indicators
        context['step_short_titles'] = {
            'course_selection': 'Course',
            'group_set_selection': 'Group Sets',
            'group_selection': 'Groups',
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
        """Process the wizard data and create Team and Student records."""
        # Get the data from each step
        form_dict = kwargs.get('form_dict', {})

        step1_data = self.get_cleaned_data_for_step('course_selection')
        step3_data = self.get_cleaned_data_for_step('group_selection')

        github_data = {}
        if self.condition_github_config():
            github_data = self.get_cleaned_data_for_step('github_config') or {}

        taiga_data = {}
        if self.condition_taiga_config():
            taiga_data = self.get_cleaned_data_for_step('taiga_config') or {}

        # Get selected groups and course
        course = step1_data.get('course')
        selected_group_ids = step3_data.get('selected_groups', [])

        if not course or not selected_group_ids:
            messages.error(
                self.request, 'Missing required data to create teams.')
            return redirect('processes:process_list')

        # Import necessary models
        from django.db import transaction
        from lms.canvas.models import CanvasGroup, CanvasGroupMembership
        from core.models import Team, Student

        # Track statistics for final message
        created_count = 0
        updated_count = 0
        student_count = 0
        errors = []

        # Create teams and students
        for group_id in selected_group_ids:
            try:
                canvas_group = CanvasGroup.objects.get(id=group_id)

                # Get GitHub and Taiga names if enabled
                github_repo_name = None
                if step1_data.get('use_github'):
                    repo_field_name = f'repo_name_{group_id}'
                    github_repo_name = github_data.get(repo_field_name, '')

                taiga_project_name = None
                if step1_data.get('use_taiga'):
                    project_field_name = f'project_name_{group_id}'
                    taiga_project_name = taiga_data.get(project_field_name, '')

                # Create or update team and associated students in a transaction
                # Removing the transaction.atomic() wrapper since it could be causing rollbacks

                # First, check if a team with this canvas_group_id already exists
                existing_teams = Team.objects.filter(
                    canvas_group_id=canvas_group.id)

                print(
                    f"Processing group {canvas_group.id}: {canvas_group.name}")

                if existing_teams.exists():
                    # Update the existing team
                    team = existing_teams.first()
                    team.name = canvas_group.name
                    team.description = canvas_group.description or ""
                    team.github_repo_name = github_repo_name
                    team.taiga_project = taiga_project_name
                    team.save()
                    created = False
                    print(f"Updated existing team: {team.id} - {team.name}")
                else:
                    # Create a new team with a unique identifier for this Canvas group
                    team = Team.objects.create(
                        name=canvas_group.name,
                        description=canvas_group.description or "",
                        github_repo_name=github_repo_name,
                        taiga_project=taiga_project_name,
                        canvas_group_id=canvas_group.id,
                    )
                    created = True
                    print(f"Created new team: {team.id} - {team.name}")

                # Track creation/update statistics
                if created:
                    created_count += 1
                else:
                    updated_count += 1

                # Update student records from group memberships
                memberships = CanvasGroupMembership.objects.filter(
                    group=canvas_group)

                print(
                    f"Found {memberships.count()} memberships for group {canvas_group.name}")

                # Create students one by one outside the transaction
                for membership in memberships:
                    try:
                        # Split the name into first and last name
                        name_parts = membership.name.split(' ', 1)
                        first_name = name_parts[0]
                        last_name = name_parts[1] if len(
                            name_parts) > 1 else ""

                        print(
                            f"Processing student: {membership.name} (ID: {membership.user_id})")

                        # Try to get existing student by canvas_user_id
                        existing_student = Student.objects.filter(
                            canvas_user_id=str(membership.user_id)
                        ).first()

                        if existing_student:
                            print(
                                f"Found existing student: {existing_student.id} - {existing_student.full_name}")
                            # Update the existing student's team
                            existing_student.team = team
                            existing_student.save()
                            print(f"Updated student team to: {team.name}")
                            student_count += 1
                        else:
                            email = membership.email
                            if not email:
                                email = f"student_{membership.user_id}@example.com"

                            print(
                                f"Creating new student: {first_name} {last_name} ({email})")

                            # Create a new student with the most basic fields first
                            student = Student.objects.create(
                                first_name=first_name,
                                last_name=last_name,
                                email=email,
                                canvas_user_id=str(membership.user_id),
                                team=team
                            )
                            print(f"Created student ID: {student.id}")
                            student_count += 1
                    except Exception as e:
                        error_msg = f"Error with student {membership.name}: {str(e)}"
                        print(f"ERROR: {error_msg}")
                        errors.append(error_msg)

            except CanvasGroup.DoesNotExist:
                errors.append(f"Group with ID {group_id} not found.")
            except Exception as e:
                errors.append(
                    f"Error creating team for group {group_id}: {str(e)}")

        # Create appropriate message
        if created_count > 0 or updated_count > 0:
            summary = []
            if created_count > 0:
                summary.append(f"{created_count} team(s) created")
            if updated_count > 0:
                summary.append(f"{updated_count} team(s) updated")
            if student_count > 0:
                summary.append(f"{student_count} student(s) assigned")

            success_msg = f"Success! {', '.join(summary)}."
            messages.success(self.request, success_msg)
        else:
            messages.warning(self.request, "No teams were created or updated.")

        # Add errors if any
        if errors:
            messages.error(
                self.request, f"Errors occurred: {'; '.join(errors)}")

        # Redirect to a success page or list view
        return redirect('processes:process_list')

    def process_step(self, form):
        """Process the form for the current step."""
        # Log form data for debugging
        step_name = self.steps.current
        print(f"Processing {step_name} form")
        print(f"Form data: {form.data}")
        print(f"Form cleaned_data: {form.cleaned_data}")
        return super().process_step(form)
